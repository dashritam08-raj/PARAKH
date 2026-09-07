from pathlib import Path

from datetime import datetime

import json

import uuid

import sqlite3


# ============================================================
# DATABASE
# ============================================================

try:
    from app.database import (
        init_database,
        get_connection,
        DATABASE_PATH,
    )
except ImportError:
    # Allows this module to be tested directly from backend/app/services.
    from ..database import (
        init_database,
        get_connection,
        DATABASE_PATH,
    )


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# Keep these names for backward compatibility with the old
# JSON-based history service. History is now stored in SQLite.
HISTORY_DIR = BASE_DIR / "inspection_history"

HISTORY_FILE = HISTORY_DIR / "inspections.json"

# SQLite database path is controlled by app.database.
# This keeps one source of truth for the database location.


HISTORY_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INITIALIZE HISTORY DATABASE
# ============================================================

def initialize_history():

    """
    Initialize the SQLite history database.

    The old implementation created inspection_history/inspections.json.
    The new implementation keeps HISTORY_DIR/HISTORY_FILE for backward
    compatibility but stores active history records in SQLite.
    """

    init_database()


initialize_history()


# ============================================================
# DATABASE HELPERS
# ============================================================

def _json_dumps(value):
    """
    Safely convert Python data to JSON text for SQLite.
    """

    return json.dumps(
        value,
        ensure_ascii=False,
        default=str
    )


def _json_loads(value, default=None):
    """
    Safely convert SQLite JSON text back to Python data.
    """

    if default is None:
        default = {}

    if not value:
        return default

    try:
        return json.loads(value)
    except Exception:
        return default


def _get_product_field(product, *keys):
    """
    Return the first non-empty product field.

    This helper supports both the original product structure and
    the normalized field names used by the current analysis backend.
    """

    if not isinstance(product, dict):
        return None

    for key in keys:
        value = product.get(key)

        if value not in (None, "", [], {}):
            return value

    return None


def _get_indexed_product_values(analysis_result):
    """
    Extract commonly used product fields for SQLite index columns.

    The complete inspection result is still stored in analysis_json.
    These columns are only for fast history searching/filtering.
    """

    product = analysis_result.get(
        "product",
        {}
    )

    if not isinstance(product, dict):
        product = {}

    product_name = _get_product_field(
        product,
        "name",
        "product_name"
    )

    brand = _get_product_field(
        product,
        "brand"
    )

    return (
        product_name,
        brand
    )


def _get_indexed_summary_values(analysis_result):
    """
    Extract summary/status/score values for SQLite columns.
    """

    summary = analysis_result.get(
        "summary",
        {}
    )

    if not isinstance(summary, dict):
        summary = {}

    compliance_score = summary.get(
        "compliance_score"
    )

    overall_status = summary.get(
        "overall_status",
        "NEEDS_REVIEW"
    )

    return (
        compliance_score,
        overall_status
    )


def _row_to_inspection(row):
    """
    Convert a SQLite row into the same inspection-record shape
    returned by the old JSON history service.
    """

    if row is None:
        return None

    analysis_result = _json_loads(
        row["analysis_json"],
        {}
    )

    if not isinstance(analysis_result, dict):
        analysis_result = {}

    # Preserve the complete saved analysis result.
    inspection = dict(analysis_result)

    # Ensure all fields expected by the old History/Details frontend
    # remain available even if an older record did not contain them.
    inspection["inspection_id"] = row["inspection_id"]

    if not inspection.get("created_at"):
        inspection["created_at"] = row["created_at"]

    inspection["filename"] = (
        row["filename"]
        if row["filename"] is not None
        else inspection.get("filename")
    )

    product = inspection.get(
        "product",
        {}
    )

    if not isinstance(product, dict):
        product = {}

    inspection["product"] = product

    summary = inspection.get(
        "summary",
        {}
    )

    if not isinstance(summary, dict):
        summary = {}

    # Database indexed values are used only when the JSON does not
    # already contain the corresponding value.
    if summary.get("overall_status") is None:
        summary["overall_status"] = (
            row["overall_status"]
            or "NEEDS_REVIEW"
        )

    if (
        summary.get("compliance_score") is None
        and row["compliance_score"] is not None
    ):
        summary["compliance_score"] = row["compliance_score"]

    inspection["summary"] = summary

    checks = inspection.get(
        "checks",
        []
    )

    if not isinstance(checks, list):
        checks = []

    inspection["checks"] = checks

    # Inspector decision fields remain at the top level exactly as
    # the original service stored them.
    inspection["inspector_decision"] = (
        row["inspector_decision"]
    )

    inspection["inspector_name"] = (
        row["inspector_name"]
    )

    inspection["inspector_remarks"] = (
        row["inspector_remarks"]
    )

    inspection["decision_timestamp"] = (
        row["decision_timestamp"]
    )

    # Preserve the final-decision convenience fields used by the
    # frontend and the original service.
    if row["inspector_decision"]:
        inspection["final_decision"] = (
            inspection.get(
                "final_decision",
                row["inspector_decision"]
            )
        )

        inspection["final_inspector"] = (
            inspection.get(
                "final_inspector",
                row["inspector_name"]
            )
        )

        inspection["final_remarks"] = (
            inspection.get(
                "final_remarks",
                row["inspector_remarks"]
            )
        )

        inspection["final_decision_at"] = (
            inspection.get(
                "final_decision_at",
                row["decision_timestamp"]
            )
        )

    return inspection


# ============================================================
# READ HISTORY
# ============================================================

def get_all_inspections():

    initialize_history()

    try:

        with get_connection() as connection:

            rows = connection.execute(
                """
                SELECT
                    id,
                    inspection_id,
                    filename,
                    status,
                    overall_status,
                    compliance_score,
                    product_name,
                    brand,
                    inspector_decision,
                    inspector_name,
                    inspector_remarks,
                    decision_timestamp,
                    created_at,
                    updated_at,
                    analysis_json
                FROM inspections
                ORDER BY datetime(created_at) DESC, id DESC
                """
            ).fetchall()

        return [
            _row_to_inspection(row)
            for row in rows
        ]

    except Exception:

        return []


# ============================================================
# WRITE HISTORY
# ============================================================

def _write_history(inspections):

    """
    Backward-compatible replacement for the old JSON writer.

    The original service used this function internally to rewrite
    inspections.json. It is intentionally retained so existing imports
    and code do not break.

    SQLite is now the source of truth. This function synchronizes the
    supplied inspection list into the SQLite database.
    """

    initialize_history()

    if not isinstance(inspections, list):
        inspections = []

    with get_connection() as connection:

        # Rebuild only when this legacy-compatible helper is explicitly
        # called. Normal save/update/delete operations use targeted SQL.
        connection.execute(
            "DELETE FROM inspections"
        )

        for inspection in inspections:

            if not isinstance(inspection, dict):
                continue

            _insert_or_replace_inspection(
                connection,
                inspection
            )

        connection.commit()


def _insert_or_replace_inspection(
    connection,
    inspection
):
    """
    Insert or replace one complete inspection record.

    The complete record is preserved inside analysis_json.
    """

    inspection_id = inspection.get(
        "inspection_id"
    )

    if not inspection_id:
        inspection_id = (
            "INS-"
            + datetime.now().strftime(
                "%Y%m%d-%H%M%S"
            )
            + "-"
            + uuid.uuid4().hex[:6].upper()
        )

        inspection["inspection_id"] = inspection_id

    created_at = inspection.get(
        "created_at"
    )

    if not created_at:
        created_at = datetime.now().isoformat()

        inspection["created_at"] = created_at

    updated_at = inspection.get(
        "updated_at",
        created_at
    )

    filename = inspection.get(
        "filename"
    )

    summary = inspection.get(
        "summary",
        {}
    )

    if not isinstance(summary, dict):
        summary = {}

    compliance_score = summary.get(
        "compliance_score"
    )

    overall_status = summary.get(
        "overall_status",
        "NEEDS_REVIEW"
    )

    product = inspection.get(
        "product",
        {}
    )

    if not isinstance(product, dict):
        product = {}

    product_name, brand = _get_indexed_product_values(
        inspection
    )

    # Keep top-level database decision columns synchronized with the
    # complete JSON record.
    inspector_decision = inspection.get(
        "inspector_decision"
    )

    inspector_name = inspection.get(
        "inspector_name"
    )

    inspector_remarks = inspection.get(
        "inspector_remarks"
    )

    decision_timestamp = inspection.get(
        "decision_timestamp"
    )

    connection.execute(
        """
        INSERT INTO inspections (
            inspection_id,
            filename,
            status,
            overall_status,
            compliance_score,
            product_name,
            brand,
            inspector_decision,
            inspector_name,
            inspector_remarks,
            decision_timestamp,
            created_at,
            updated_at,
            analysis_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(inspection_id) DO UPDATE SET
            filename = excluded.filename,
            status = excluded.status,
            overall_status = excluded.overall_status,
            compliance_score = excluded.compliance_score,
            product_name = excluded.product_name,
            brand = excluded.brand,
            inspector_decision = excluded.inspector_decision,
            inspector_name = excluded.inspector_name,
            inspector_remarks = excluded.inspector_remarks,
            decision_timestamp = excluded.decision_timestamp,
            created_at = excluded.created_at,
            updated_at = excluded.updated_at,
            analysis_json = excluded.analysis_json
        """,
        (
            inspection_id,
            filename,
            overall_status,
            overall_status,
            compliance_score,
            product_name,
            brand,
            inspector_decision,
            inspector_name,
            inspector_remarks,
            decision_timestamp,
            created_at,
            updated_at,
            _json_dumps(inspection)
        )
    )


# ============================================================
# SAVE INSPECTION
# ============================================================

def save_inspection(
    analysis_result,
    filename=None
):

    initialize_history()

    if not isinstance(analysis_result, dict):
        analysis_result = {}

    summary = analysis_result.get(
        "summary",
        {}
    )

    product = analysis_result.get(
        "product",
        {}
    )

    if not isinstance(summary, dict):
        summary = {}

    if not isinstance(product, dict):
        product = {}


    # --------------------------------------------------------
    # Generate unique inspection ID
    # --------------------------------------------------------

    inspection_id = (

        "INS-"

        + datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )

        + "-"

        + uuid.uuid4().hex[:6].upper()

    )


    # --------------------------------------------------------
    # Create inspection record
    # --------------------------------------------------------

    # Start with the complete analysis result so no OCR, extracted
    # data, compliance evidence, candidates, detection information,
    # rules, or other backend-generated information is lost.
    inspection = dict(
        analysis_result
    )

    inspection.update({

        "inspection_id":
            inspection_id,


        "created_at":
            datetime.now().isoformat(),


        "filename":
            filename or
            analysis_result.get(
                "filename"
            ),


        # ====================================================
        # PRODUCT
        # ====================================================

        "product": {

            "name":
                product.get(
                    "name"
                ),

            "brand":
                product.get(
                    "brand"
                ),

            "commodity":
                product.get(
                    "commodity"
                ),

            "net_quantity":
                product.get(
                    "net_quantity"
                ),

            "mrp":
                product.get(
                    "mrp"
                ),

            "manufacturer":
                product.get(
                    "manufacturer"
                ),

            "packaging_date":
                product.get(
                    "packaging_date"
                ),

            "best_before":
                product.get(
                    "best_before"
                ),

            "food_license":
                product.get(
                    "food_license"
                ),

        },


        # ====================================================
        # SUMMARY
        # ====================================================

        "summary": {

            "compliance_score":
                summary.get(
                    "compliance_score"
                ),

            "overall_status":
                summary.get(
                    "overall_status",
                    "NEEDS_REVIEW"
                ),

            "passed":
                summary.get(
                    "passed",
                    0
                ),

            "failed":
                summary.get(
                    "failed",
                    0
                ),

            "needs_review":
                summary.get(
                    "needs_review",
                    0
                ),

            "not_checked":
                summary.get(
                    "not_checked",
                    0
                ),

            "total_checks":
                summary.get(
                    "total_checks",
                    0
                ),

        },


        # ====================================================
        # COMPLIANCE CHECKS
        # ====================================================

        "checks":
            analysis_result.get(
                "checks",
                []
            ),


        # ====================================================
        # INSPECTOR DECISION
        #
        # Empty initially.
        # Filled after manual verification.
        # ====================================================

        "inspector_decision":
            None,

        "inspector_name":
            None,

        "inspector_remarks":
            None,

        "decision_timestamp":
            None,

    })


    # ========================================================
    # INSERT NEWEST FIRST
    # ========================================================

    # Keep the original newest-first behavior conceptually.
    # SQLite returns records ordered by created_at/id descending.


    # ========================================================
    # KEEP LATEST 100
    # ========================================================

    # Keep the original history retention limit.
    # New records are inserted first and the oldest records are
    # removed after the 100-record limit is exceeded.


    # ========================================================
    # SAVE
    # ========================================================

    with get_connection() as connection:

        _insert_or_replace_inspection(
            connection,
            inspection
        )

        # ----------------------------------------------------
        # Keep latest 100
        # ----------------------------------------------------

        connection.execute(
            """
            DELETE FROM inspections
            WHERE id NOT IN (
                SELECT id
                FROM inspections
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT 100
            )
            """
        )

        connection.commit()


    return inspection


# ============================================================
# FIND INSPECTION
# ============================================================

def get_inspection(
    inspection_id
):

    initialize_history()

    if not inspection_id:
        return None

    try:

        with get_connection() as connection:

            row = connection.execute(
                """
                SELECT
                    id,
                    inspection_id,
                    filename,
                    status,
                    overall_status,
                    compliance_score,
                    product_name,
                    brand,
                    inspector_decision,
                    inspector_name,
                    inspector_remarks,
                    decision_timestamp,
                    created_at,
                    updated_at,
                    analysis_json
                FROM inspections
                WHERE inspection_id = ?
                LIMIT 1
                """,
                (
                    inspection_id,
                )
            ).fetchone()

        return _row_to_inspection(
            row
        )

    except Exception:

        return None


# ============================================================
# UPDATE INSPECTOR FINAL DECISION
# ============================================================

def update_inspection_decision(
    inspection_id,
    decision,
    inspector_name="PARAKH Inspector",
    remarks=""
):

    initialize_history()


    # ========================================================
    # VALIDATE DECISION
    # ========================================================

    decision = str(
        decision or ""
    ).strip().upper()


    allowed_decisions = {

        "COMPLIANT",

        "NON_COMPLIANT",

    }


    if decision not in allowed_decisions:

        raise ValueError(
            "Decision must be "
            "COMPLIANT or "
            "NON_COMPLIANT."
        )


    # ========================================================
    # VALIDATE INSPECTOR NAME
    # ========================================================

    inspector_name = str(
        inspector_name or ""
    ).strip()


    if not inspector_name:

        inspector_name = (
            "PARAKH Inspector"
        )


    # ========================================================
    # NORMALIZE REMARKS
    # ========================================================

    remarks = str(
        remarks or ""
    ).strip()


    # ========================================================
    # NON-COMPLIANT REQUIRES REMARKS
    # ========================================================

    if (
        decision == "NON_COMPLIANT"
        and not remarks
    ):

        raise ValueError(
            "Inspector remarks are "
            "required when marking "
            "an inspection "
            "NON_COMPLIANT."
        )


    # ========================================================
    # LOAD INSPECTION
    # ========================================================

    target_inspection = get_inspection(
        inspection_id
    )


    # ========================================================
    # NOT FOUND
    # ========================================================

    if target_inspection is None:

        return None


    # ========================================================
    # KEEP ORIGINAL AI STATUS
    #
    # This is useful for your judges:
    #
    # AI status:
    # NEEDS_REVIEW
    #
    # Inspector decision:
    # COMPLIANT
    #
    # So we can clearly show that AI
    # flagged it and the human Inspector
    # made the final decision.
    # ========================================================

    summary = target_inspection.get(
        "summary"
    )


    if not isinstance(
        summary,
        dict
    ):

        summary = {}

        target_inspection[
            "summary"
        ] = summary


    if (
        "ai_overall_status"
        not in summary
    ):

        summary[
            "ai_overall_status"
        ] = summary.get(
            "overall_status",
            "NEEDS_REVIEW"
        )


    # ========================================================
    # SAVE FINAL INSPECTOR DECISION
    # ========================================================

    target_inspection[
        "inspector_decision"
    ] = decision


    target_inspection[
        "inspector_name"
    ] = inspector_name


    target_inspection[
        "inspector_remarks"
    ] = remarks


    target_inspection[
        "decision_timestamp"
    ] = datetime.now().isoformat()


    # ========================================================
    # UPDATE FINAL OVERALL STATUS
    #
    # Dashboard / History should use this final status.
    # ========================================================

    summary[
        "overall_status"
    ] = decision


    # ========================================================
    # OPTIONAL FINAL DECISION OBJECT
    #
    # This makes the saved JSON easier to understand
    # and gives the frontend another reliable source.
    # ========================================================

    target_inspection[
        "final_decision"
    ] = decision


    target_inspection[
        "final_inspector"
    ] = inspector_name


    target_inspection[
        "final_remarks"
    ] = remarks


    target_inspection[
        "final_decision_at"
    ] = target_inspection[
        "decision_timestamp"
    ]


    # ========================================================
    # SAVE UPDATED HISTORY
    # ========================================================

    target_inspection["updated_at"] = (
        datetime.now().isoformat()
    )

    with get_connection() as connection:

        _insert_or_replace_inspection(
            connection,
            target_inspection
        )

        connection.commit()


    # ========================================================
    # RETURN UPDATED RECORD
    # ========================================================

    return target_inspection


# ============================================================
# DELETE INSPECTION
# ============================================================

def delete_inspection(
    inspection_id
):

    initialize_history()

    if not inspection_id:
        return False

    # ========================================================
    # DELETE TARGET INSPECTION
    # ========================================================

    try:

        with get_connection() as connection:

            cursor = connection.execute(
                """
                DELETE FROM inspections
                WHERE inspection_id = ?
                """,
                (
                    inspection_id,
                )
            )

            deleted = (
                cursor.rowcount > 0
            )

            connection.commit()

        return deleted

    except Exception:

        return False


# ============================================================
# INSPECTION COUNT
# ============================================================

def get_inspection_count():

    initialize_history()

    try:

        with get_connection() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM inspections
                """
            ).fetchone()

        return int(
            row["count"]
        )

    except Exception:

        return 0
