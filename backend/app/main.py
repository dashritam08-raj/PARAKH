from pathlib import Path
import json

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Request,
    Response,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.services.ocr_service import (
    extract_text_from_image
)

from app.services.product_extractor import (
    extract_product_fields
)

from app.services.compliance_engine import (
    evaluate_compliance
)

from app.services.report_service import (
    generate_inspection_report
)

from app.services.history_service import (
    save_inspection,
    get_all_inspections,
    get_inspection,
    delete_inspection,
    update_inspection_decision,
)

from app.auth import (
    authenticate_user,
    create_session,
    create_user,
    get_current_user,
    logout_session,
    set_session_cookie,
    user_to_dict,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RULES_FILE = (
    BASE_DIR
    / "legal_data"
    / "rules"
    / "compliance_rules.json"
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="PARAKH API",
    description=(
        "AI-powered Legal Metrology "
        "Packaged Commodity Compliance API"
    ),
    version="1.0.0",
)

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

from app.database import init_database

init_database()


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.0.107:5173",
        "https://pension-actors-approval-wishing.trycloudflare.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LOAD LEGAL RULES
# ============================================================

def load_rules():

    if not RULES_FILE.exists():

        return {
            "error": "compliance_rules.json not found",
            "rules": [],
        }

    try:

        with open(
            RULES_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except Exception as error:

        return {
            "error": (
                f"Could not load legal rules: {error}"
            ),
            "rules": [],
        }


# ============================================================
# AUTHENTICATION
# ============================================================

@app.post("/auth/register")
async def register(
    response: Response,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    """
    Register a PARAKH inspector account.

    Passwords are hashed with Argon2id inside app.auth.
    The raw password is never stored in SQLite.
    """

    try:

        user = create_user(
            name=name,
            email=email,
            password=password,
            role="INSPECTOR",
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "Registration error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Could not create account.",
        )

    session = create_session(
        user["id"]
    )

    set_session_cookie(
        response,
        session["token"],
        session["expires_at"],
    )

    return {
        "status": "success",
        "message": "Account created successfully.",
        "user": user_to_dict(user),
    }


@app.post("/auth/login")
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
):
    """
    Authenticate a user and create an HttpOnly session cookie.
    """

    user = authenticate_user(
        email=email,
        password=password,
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    session = create_session(
        user["id"]
    )

    set_session_cookie(
        response,
        session["token"],
        session["expires_at"],
    )

    return {
        "status": "success",
        "message": "Login successful.",
        "user": user_to_dict(user),
    }


@app.post("/auth/logout")
async def logout(
    request: Request,
    response: Response,
):
    """
    Revoke the current session and clear its HttpOnly cookie.
    """

    logout_session(
        request,
        response,
    )

    return {
        "status": "success",
        "message": "Logout successful.",
    }


@app.get("/auth/me")
def auth_me(
    request: Request,
):
    """
    Return the currently authenticated user.
    """

    user = get_current_user(
        request
    )

    return {
        "status": "success",
        "user": user_to_dict(user),
    }


# ============================================================
# ROOT / HEALTH CHECK
# ============================================================

@app.get("/")
def root():

    return {
        "message": "PARAKH backend is running",
        "status": "online",
        "version": "1.0.0",
    }


# ============================================================
# RULES ENDPOINT
# ============================================================

@app.get("/rules")
def get_rules():

    rules = load_rules()

    if "error" in rules:

        raise HTTPException(
            status_code=500,
            detail=rules["error"],
        )

    return rules


# ============================================================
# OCR TEST
# ============================================================

@app.post("/ocr-test")
async def ocr_test(
    request: Request,
    file: UploadFile = File(...),
):
    get_current_user(request)

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    image_data = await file.read()

    if not image_data:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    try:

        ocr_text = extract_text_from_image(
            image_data
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"OCR failed: {error}",
        )

    return {
        "filename": file.filename,
        "ocr_text": ocr_text,
        "text_length": len(ocr_text),
    }


# ============================================================
# NORMALIZE PRODUCT FIELDS
# ============================================================

def normalize_product_fields(
    product_fields,
):

    normalized = dict(
        product_fields
    )

    confidence_data = {}

    # --------------------------------------------------------
    # Manufacturer
    # --------------------------------------------------------

    manufacturer = normalized.get(
        "manufacturer"
    )

    if manufacturer:

        normalized[
            "manufacturer_or_packer_or_importer"
        ] = manufacturer

    # --------------------------------------------------------
    # MRP
    # --------------------------------------------------------

    mrp = normalized.get(
        "mrp"
    )

    if mrp:

        normalized[
            "retail_sale_price"
        ] = mrp

    # --------------------------------------------------------
    # Packaging date
    # --------------------------------------------------------

    packaging_date = normalized.get(
        "packaging_date"
    )

    if packaging_date:

        normalized[
            "manufacture_or_prepack_date"
        ] = packaging_date

    # --------------------------------------------------------
    # Consumer complaint contact
    # --------------------------------------------------------

    contact = normalized.get(
        "consumer_complaint_contact"
    )

    if isinstance(
        contact,
        dict,
    ):

        confidence_data[
            "consumer_complaint_contact"
        ] = contact

        normalized[
            "consumer_complaint_contact"
        ] = contact.get(
            "value"
        )

    return (
        normalized,
        confidence_data,
    )


# ============================================================
# BUILD FRONTEND PRODUCT OBJECT
# ============================================================

def build_product_response(
    product_fields,
):

    return {

        "name":
            product_fields.get(
                "product_name"
            ),

        "brand":
            product_fields.get(
                "brand"
            ),

        "commodity":
            product_fields.get(
                "commodity_name"
            ),

        "net_quantity":
            product_fields.get(
                "net_quantity"
            ),

        "mrp":
            product_fields.get(
                "mrp"
            ),

        "unit_sale_price":
            product_fields.get(
                "unit_sale_price"
            ),

        "manufacturer":
            product_fields.get(
                "manufacturer"
            ),

        "packaging_date":
            product_fields.get(
                "packaging_date"
            ),

        "best_before":
            product_fields.get(
                "best_before"
            ),

        "consumer_contact":
            product_fields.get(
                "consumer_complaint_contact"
            ),

        "food_license":
            product_fields.get(
                "food_license"
            ),
    }


# ============================================================
# BUILD DETAILED EXTRACTION DATA
# ============================================================

def build_extracted_data(
    product_fields,
    confidence_data,
):

    extracted_data = {}

    for field, value in product_fields.items():

        # ----------------------------------------------------
        # Confidence-aware field
        # ----------------------------------------------------

        if field in confidence_data:

            metadata = confidence_data[
                field
            ]

            extracted_data[field] = {

                "value":
                    metadata.get(
                        "value"
                    ),

                "confidence":
                    metadata.get(
                        "confidence",
                        0.0,
                    ),

                "status":
                    metadata.get(
                        "status",
                        "NOT_DETECTED",
                    ),

                "evidence":
                    metadata.get(
                        "evidence",
                        [],
                    ),

                "candidates":
                    metadata.get(
                        "candidates",
                        [],
                    ),
            }

            continue

        # ----------------------------------------------------
        # Normal field
        # ----------------------------------------------------

        if (
            value is not None
            and str(value).strip()
        ):

            extracted_data[field] = {

                "value":
                    value,

                "confidence":
                    0.95,

                "status":
                    "DETECTED",

                "evidence":
                    [],

                "candidates":
                    [],
            }

        else:

            extracted_data[field] = {

                "value":
                    None,

                "confidence":
                    0.0,

                "status":
                    "NOT_DETECTED",

                "evidence":
                    [],

                "candidates":
                    [],
            }

    return extracted_data


# ============================================================
# DETECTION STATISTICS
# ============================================================

def calculate_detection(
    extracted_data,
):

    total_fields = len(
        extracted_data
    )

    detected_fields = sum(

        1

        for field
        in extracted_data.values()

        if (
            field.get("value")
            is not None
        )
        and
        str(
            field.get("value")
        ).strip()
    )

    if total_fields > 0:

        percentage = round(
            (
                detected_fields
                /
                total_fields
            )
            * 100,
            2,
        )

    else:

        percentage = 0

    return {

        "detected_fields":
            detected_fields,

        "total_fields":
            total_fields,

        "detection_percentage":
            percentage,
    }


# ============================================================
# ANALYZE PRODUCT
# ============================================================

@app.post("/analyze")
async def analyze_product(
    request: Request,
    file: UploadFile = File(...),
):
    get_current_user(request)

    # ========================================================
    # 1. FILE VALIDATION
    # ========================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    image_data = await file.read()

    if not image_data:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    file_size = len(
        image_data
    )


    # ========================================================
    # 2. LOAD LEGAL RULES
    # ========================================================

    legal_rules = load_rules()

    if "error" in legal_rules:

        raise HTTPException(
            status_code=500,
            detail=legal_rules["error"],
        )

    if not isinstance(legal_rules.get("rules"), list) or not legal_rules.get("rules"):

        raise HTTPException(
            status_code=500,
            detail="No compliance rules are loaded. Check legal_data/rules/compliance_rules.json.",
        )


    # ========================================================
    # 3. OCR
    # ========================================================

    try:

        ocr_text = extract_text_from_image(
            image_data
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"OCR failed: {error}",
        )


    if not ocr_text:

        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text detected "
                "in image."
            ),
        )


    # ========================================================
    # 4. PRODUCT EXTRACTION
    # ========================================================

    try:

        product_fields = extract_product_fields(
            ocr_text
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Product extraction failed: "
                f"{error}"
            ),
        )


    # ========================================================
    # 5. NORMALIZATION
    # ========================================================

    (
        product_fields,
        confidence_data,
    ) = normalize_product_fields(
        product_fields
    )


    # ========================================================
    # 6. DETAILED EXTRACTION
    # ========================================================

    extracted_data = build_extracted_data(

        product_fields,

        confidence_data,

    )


    # ========================================================
    # 7. DETECTION STATISTICS
    # ========================================================

    detection = calculate_detection(
        extracted_data
    )


    # ========================================================
    # 8. COMPLIANCE ENGINE
    # ========================================================

    try:

        compliance_result = evaluate_compliance(

            legal_rules,

            product_fields,

            confidence_data,

        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Compliance evaluation failed: "
                f"{error}"
            ),
        )


    # ========================================================
    # 9. COMPLIANCE CHECKS
    # ========================================================

    checks = compliance_result.get(
        "checks",
        [],
    )


    # ========================================================
    # 10. COMPLIANCE SUMMARY
    # ========================================================

    summary = compliance_result.get(

        "summary",

        {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "needs_review": 0,
            "not_checked": 0,
            "compliance_score": None,
            "overall_status": "PENDING",
        },

    )


    # ========================================================
    # 11. PRODUCT
    # ========================================================

    product = build_product_response(
        product_fields
    )


    # ========================================================
    # 12. FINAL ANALYSIS RESULT
    # ========================================================

    analysis_result = {

        "status":
            "Analysis Complete",

        "filename":
            file.filename,

        "file_size":
            file_size,

        "legal_engine":
            "PARAKH Legal Metrology Rules",

        "regulation":
            legal_rules.get(
                "regulation",
                (
                    "Legal Metrology "
                    "(Packaged Commodities) "
                    "Rules, 2011"
                ),
            ),

        "rule_version":
            legal_rules.get(
                "schema_version",
                "unknown",
            ),

        "ocr_text":
            ocr_text,

        "ocr_text_length":
            len(ocr_text),

        "product":
            product,

        "extracted_data":
            extracted_data,

        "detection":
            detection,

        "checks":
            checks,

        "summary":
            summary,

        # ----------------------------------------------------
        # Inspector decision starts empty.
        # ----------------------------------------------------

        "inspector_decision":
            None,

        "inspector_name":
            None,

        "inspector_remarks":
            None,

        "decision_timestamp":
            None,

        "message":
            (
                "OCR, product extraction, "
                "confidence analysis and "
                "rule-based compliance "
                "evaluation completed."
            ),
    }


    # ========================================================
    # 13. SAVE TO INSPECTION HISTORY
    # ========================================================

    try:

        saved_inspection = save_inspection(

            analysis_result,

            file.filename,

        )

        if saved_inspection:

            analysis_result[
                "inspection_id"
            ] = saved_inspection.get(
                "inspection_id"
            )

    except Exception as error:

        # History failure must NEVER
        # break successful analysis.

        print(
            "WARNING: Could not save "
            f"inspection history: {error}"
        )


    # ========================================================
    # 14. RETURN
    # ========================================================

    return analysis_result


# ============================================================
# INSPECTION HISTORY
# ============================================================

@app.get("/history")
def inspection_history(
    request: Request,
):
    get_current_user(request)

    inspections = get_all_inspections()

    return {

        "status":
            "success",

        "count":
            len(inspections),

        "inspections":
            inspections,
    }


# ============================================================
# SINGLE INSPECTION
# ============================================================

@app.get(
    "/history/{inspection_id}"
)
def inspection_details(
    inspection_id: str,
    request: Request,
):
    get_current_user(request)

    inspection = get_inspection(
        inspection_id
    )


    if inspection is None:

        raise HTTPException(
            status_code=404,
            detail="Inspection not found",
        )


    return {

        "status":
            "success",

        "inspection":
            inspection,
    }


# ============================================================
# INSPECTOR FINAL DECISION
# ============================================================

@app.patch(
    "/history/{inspection_id}/decision"
)
async def update_inspector_decision_endpoint(
    request: Request,
    inspection_id: str,
    decision: dict,
):
    get_current_user(request)

    # --------------------------------------------------------
    # Check inspection
    # --------------------------------------------------------

    inspection = get_inspection(
        inspection_id
    )

    if inspection is None:

        raise HTTPException(
            status_code=404,
            detail="Inspection not found",
        )


    # --------------------------------------------------------
    # Read decision
    # --------------------------------------------------------

    requested_decision = str(

        decision.get(
            "decision",
            "",
        )

    ).strip().upper()


    # --------------------------------------------------------
    # Validate decision
    # --------------------------------------------------------

    if requested_decision not in {

        "COMPLIANT",

        "NON_COMPLIANT",

    }:

        raise HTTPException(

            status_code=400,

            detail=(
                "Decision must be "
                "COMPLIANT or "
                "NON_COMPLIANT."
            ),

        )


    # --------------------------------------------------------
    # Inspector name
    # --------------------------------------------------------

    inspector_name = str(

        decision.get(
            "inspector_name",
            "PARAKH Inspector",
        )

    ).strip()


    if not inspector_name:

        inspector_name = (
            "PARAKH Inspector"
        )


    # --------------------------------------------------------
    # Remarks
    # --------------------------------------------------------

    remarks = str(

        decision.get(
            "remarks",
            "",
        )

    ).strip()


    # --------------------------------------------------------
    # Non-compliant should have remarks
    # --------------------------------------------------------

    if (
        requested_decision
        == "NON_COMPLIANT"
        and not remarks
    ):

        raise HTTPException(

            status_code=400,

            detail=(
                "Inspector remarks are "
                "required when marking "
                "an inspection "
                "non-compliant."
            ),

        )


    # --------------------------------------------------------
    # SAVE DECISION
    # --------------------------------------------------------

    try:

        updated = update_inspection_decision(

            inspection_id=
                inspection_id,

            decision=
                requested_decision,

            inspector_name=
                inspector_name,

            remarks=
                remarks,

        )

    except Exception as error:

        print(
            "Inspector decision update error:",
            error,
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "Could not save "
                "Inspector decision."
            ),

        )


    if updated is None:

        raise HTTPException(

            status_code=404,

            detail="Inspection not found",

        )


    return {

        "status":
            "success",

        "message":
            "Inspector decision saved successfully.",

        "inspection":
            updated,

    }


# ============================================================
# DELETE INSPECTION
# ============================================================

@app.delete(
    "/history/{inspection_id}"
)
def remove_inspection(
    inspection_id: str,
    request: Request,
):
    get_current_user(request)

    deleted = delete_inspection(
        inspection_id
    )


    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Inspection not found",
        )


    return {

        "status":
            "success",

        "message":
            "Inspection deleted successfully",

    }


# ============================================================
# GENERATE INSPECTION REPORT
# ============================================================

@app.post("/generate-report")
async def generate_report(
    request: Request,
    file: UploadFile = File(...),
    analysis_result: str = Form(...),
):
    get_current_user(request)
    # --------------------------------------------------------
    # 1. Validate uploaded image
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    image_data = await file.read()

    if not image_data:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # --------------------------------------------------------
    # 2. Validate analysis result from frontend
    # --------------------------------------------------------

    if not analysis_result:
        raise HTTPException(
            status_code=400,
            detail="Analysis result is missing.",
        )

    try:
        parsed_analysis = json.loads(
            analysis_result
        )
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid analysis result JSON: {error}",
        )

    if not isinstance(parsed_analysis, dict):
        raise HTTPException(
            status_code=400,
            detail="Analysis result must be a JSON object.",
        )

    # --------------------------------------------------------
    # 3. Save uploaded image temporarily
    # --------------------------------------------------------

    upload_dir = BASE_DIR / "uploads"
    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = Path(
        file.filename
    ).name

    image_path = upload_dir / safe_filename

    try:
        with open(
            image_path,
            "wb",
        ) as image_file:
            image_file.write(image_data)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save uploaded image: {error}",
        )

    # --------------------------------------------------------
    # 4. Generate PDF using report_service.py
    # --------------------------------------------------------

    try:
        report_result = generate_inspection_report(
            parsed_analysis,
            str(image_path),
        )
    except Exception as error:
        print(
            "PDF generation error:",
            error,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {error}",
        )

    # --------------------------------------------------------
    # 5. Read report path
    #
    # Supports both:
    #   {"path": "..."}
    # and a direct path string.
    # --------------------------------------------------------

    if isinstance(
        report_result,
        dict,
    ):
        report_path = report_result.get(
            "path"
        )
    else:
        report_path = report_result

    if not report_path:
        raise HTTPException(
            status_code=500,
            detail="Report file path was not returned.",
        )

    report_path = Path(
        report_path
    )

    # --------------------------------------------------------
    # 6. Verify generated PDF
    # --------------------------------------------------------

    if not report_path.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Generated report file not found: "
                f"{report_path}"
            ),
        )

    if report_path.stat().st_size <= 0:
        raise HTTPException(
            status_code=500,
            detail="Generated PDF is empty.",
        )

    # --------------------------------------------------------
    # 7. Return PDF to browser
    # --------------------------------------------------------

    return FileResponse(
        path=str(
            report_path
        ),
        media_type="application/pdf",
        filename="PARAKH-Inspection-Report.pdf",
    )
