from pathlib import Path
from datetime import datetime
import html
import uuid

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

REPORT_DIR = BASE_DIR / "generated_reports"

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# HELPERS
# ============================================================

def safe_text(value, fallback="Not detected"):
    """
    Safely convert a value into text suitable for ReportLab.
    """
    if value is None:
        return fallback

    if value == "":
        return fallback

    return html.escape(str(value))


def normalize_status(status):
    """
    Normalize compliance status.
    """

    return (
        str(status or "PENDING")
        .upper()
        .replace("-", "_")
        .strip()
    )


def get_status_color(status):
    """
    Return text color according to compliance status.
    """

    status = normalize_status(status)

    if status in ["PASS", "COMPLIANT"]:
        return colors.HexColor("#15803D")

    if status in ["FAIL", "NON_COMPLIANT"]:
        return colors.HexColor("#DC2626")

    if status in ["NEEDS_REVIEW", "REVIEW"]:
        return colors.HexColor("#D97706")

    return colors.HexColor("#64748B")


def get_status_background(status):
    """
    Return background color according to status.
    """

    status = normalize_status(status)

    if status in ["PASS", "COMPLIANT"]:
        return colors.HexColor("#ECFDF3")

    if status in ["FAIL", "NON_COMPLIANT"]:
        return colors.HexColor("#FEF2F2")

    if status in ["NEEDS_REVIEW", "REVIEW"]:
        return colors.HexColor("#FFFBEB")

    return colors.HexColor("#F1F5F9")


def get_status_label(status):
    """
    Human readable compliance status.
    """

    status = normalize_status(status)

    labels = {
        "PASS": "PASS",
        "COMPLIANT": "COMPLIANT",
        "FAIL": "FAIL",
        "NON_COMPLIANT": "NON-COMPLIANT",
        "NEEDS_REVIEW": "NEEDS REVIEW",
        "REVIEW": "NEEDS REVIEW",
        "NOT_CHECKED": "NOT CHECKED",
        "PENDING": "PENDING",
    }

    return labels.get(
        status,
        status.replace("_", " "),
    )


def confidence_percent(value):
    """
    Convert confidence to 0-100 percentage.
    Supports both 0-1 and 0-100 input.
    """

    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0

    if number <= 1:
        number *= 100

    number = max(
        0,
        min(100, number),
    )

    return round(number)


def get_summary(analysis_result):
    """
    Safely obtain compliance summary.
    """

    summary = (
        analysis_result.get("summary")
        or {}
    )

    compliance = (
        analysis_result.get("compliance")
        or {}
    )

    score = (
        summary.get("compliance_score")
        if summary.get("compliance_score")
        is not None
        else summary.get("score")
        if summary.get("score")
        is not None
        else compliance.get("score")
    )

    status = (
        summary.get("overall_status")
        or summary.get("status")
        or compliance.get("status")
        or "PENDING"
    )

    return {
        "score": score,
        "status": normalize_status(status),
        "passed": summary.get(
            "passed",
            compliance.get("passed", 0),
        ),
        "failed": summary.get(
            "failed",
            compliance.get("failed", 0),
        ),
        "needs_review": summary.get(
            "needs_review",
            compliance.get(
                "needs_review",
                0,
            ),
        ),
        "not_checked": summary.get(
            "not_checked",
            compliance.get(
                "not_checked",
                0,
            ),
        ),
    }


# ============================================================
# PAGE HEADER / FOOTER
# ============================================================

def draw_page(canvas, document):
    """
    Draw header and footer on every PDF page.
    """

    canvas.saveState()

    page_width, page_height = A4

    # --------------------------------------------------------
    # TOP LINE
    # --------------------------------------------------------

    canvas.setStrokeColor(
        colors.HexColor("#17243B")
    )

    canvas.setLineWidth(1)

    canvas.line(
        15 * mm,
        page_height - 10 * mm,
        page_width - 15 * mm,
        page_height - 10 * mm,
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    canvas.setFont(
        "Helvetica-Bold",
        8,
    )

    canvas.setFillColor(
        colors.HexColor("#17243B")
    )

    canvas.drawString(
        15 * mm,
        page_height - 8 * mm,
        "PARAKH",
    )

    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.setFillColor(
        colors.HexColor("#64748B")
    )

    canvas.drawRightString(
        page_width - 15 * mm,
        page_height - 8 * mm,
        "Legal Metrology Compliance Inspection",
    )

    # --------------------------------------------------------
    # FOOTER LINE
    # --------------------------------------------------------

    canvas.setStrokeColor(
        colors.HexColor("#E2E8F0")
    )

    canvas.setLineWidth(0.5)

    canvas.line(
        15 * mm,
        11 * mm,
        page_width - 15 * mm,
        11 * mm,
    )

    # --------------------------------------------------------
    # FOOTER TEXT
    # --------------------------------------------------------

    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.setFillColor(
        colors.HexColor("#64748B")
    )

    canvas.drawString(
        15 * mm,
        7 * mm,
        "Generated by PARAKH",
    )

    canvas.drawRightString(
        page_width - 15 * mm,
        7 * mm,
        f"Page {canvas.getPageNumber()}",
    )

    canvas.restoreState()


# ============================================================
# MAIN PDF FUNCTION
# ============================================================

def generate_inspection_report(
    analysis_result,
    image_path=None,
):
    """
    Generate a complete PARAKH inspection PDF.

    Parameters:
        analysis_result: dictionary returned by /analyze
        image_path: optional uploaded product image

    Returns:
        {
            "report_id": "...",
            "filename": "...",
            "path": "..."
        }
    """

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    if not isinstance(
        analysis_result,
        dict,
    ):
        analysis_result = {}

    # --------------------------------------------------------
    # REPORT ID
    # --------------------------------------------------------

    report_id = (
        "PARAKH-"
        + datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )
        + "-"
        + uuid.uuid4().hex[:6].upper()
    )

    filename = (
        f"{report_id}.pdf"
    )

    output_path = (
        REPORT_DIR / filename
    )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=18 * mm,
        bottomMargin=17 * mm,
        title=(
            f"PARAKH Inspection Report "
            f"{report_id}"
        ),
        author="PARAKH",
    )

    # --------------------------------------------------------
    # STYLES
    # --------------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PARAKHTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor(
            "#17243B"
        ),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "PARAKHSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor(
            "#64748B"
        ),
        spaceAfter=16,
    )

    heading_style = ParagraphStyle(
        "PARAKHHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor(
            "#17243B"
        ),
        spaceBefore=12,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "PARAKHNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor(
            "#334155"
        ),
    )

    small_style = ParagraphStyle(
        "PARAKHSmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor(
            "#64748B"
        ),
    )

    center_style = ParagraphStyle(
        "PARAKHCenter",
        parent=normal_style,
        alignment=TA_CENTER,
    )

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    summary = get_summary(
        analysis_result
    )

    product = (
        analysis_result.get("product")
        or {}
    )

    checks = (
        analysis_result.get("checks")
        or []
    )

    # --------------------------------------------------------
    # STORY
    # --------------------------------------------------------

    story = []

    # ========================================================
    # HEADER
    # ========================================================

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        Paragraph(
            "PARAKH",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Legal Metrology Compliance Inspection Report",
            subtitle_style,
        )
    )

    # ========================================================
    # STATUS BANNER
    # ========================================================

    final_status = summary[
        "status"
    ]

    status_banner = Table(
        [[
            Paragraph(
                "<b>FINAL INSPECTION STATUS</b>",
                center_style,
            ),
            Paragraph(
                (
                    f"<b>"
                    f"{safe_text(get_status_label(final_status))}"
                    f"</b>"
                ),
                center_style,
            ),
        ]],
        colWidths=[
            80 * mm,
            95 * mm,
        ],
    )

    status_banner.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, 0),
                colors.HexColor("#F1F5F9"),
            ),
            (
                "BACKGROUND",
                (1, 0),
                (1, 0),
                get_status_background(
                    final_status
                ),
            ),
            (
                "TEXTCOLOR",
                (1, 0),
                (1, 0),
                get_status_color(
                    final_status
                ),
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.6,
                colors.HexColor("#CBD5E1"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                9,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                9,
            ),
        ])
    )

    story.append(
        status_banner
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # ========================================================
    # INSPECTION INFORMATION
    # ========================================================

    story.append(
        Paragraph(
            "Inspection Information",
            heading_style,
        )
    )

    regulation = analysis_result.get(
        "regulation",
        (
            "Legal Metrology "
            "(Packaged Commodities) "
            "Rules, 2011"
        ),
    )

    legal_engine = analysis_result.get(
        "legal_engine",
        "PARAKH Legal Metrology Rules",
    )

    inspection_info = [
        [
            Paragraph(
                "<b>Inspection ID</b>",
                normal_style,
            ),
            Paragraph(
                safe_text(report_id),
                normal_style,
            ),
        ],
        [
            Paragraph(
                "<b>Inspection Date</b>",
                normal_style,
            ),
            Paragraph(
                datetime.now().strftime(
                    "%d %B %Y, %I:%M %p"
                ),
                normal_style,
            ),
        ],
        [
            Paragraph(
                "<b>Regulation</b>",
                normal_style,
            ),
            Paragraph(
                safe_text(regulation),
                normal_style,
            ),
        ],
        [
            Paragraph(
                "<b>Legal Engine</b>",
                normal_style,
            ),
            Paragraph(
                safe_text(legal_engine),
                normal_style,
            ),
        ],
    ]

    info_table = Table(
        inspection_info,
        colWidths=[
            45 * mm,
            130 * mm,
        ],
    )

    info_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#F8FAFC"),
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#E2E8F0"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
        ])
    )

    story.append(
        info_table
    )

    # ========================================================
    # PACKAGE IMAGE
    # ========================================================

    if image_path:

        image_file = Path(
            image_path
        )

        if image_file.exists():

            try:

                story.append(
                    Paragraph(
                        "Package Image",
                        heading_style,
                    )
                )

                product_image = Image(
                    str(image_file)
                )

                product_image.drawWidth = (
                    65 * mm
                )

                product_image.drawHeight = (
                    65 * mm
                )

                image_table = Table(
                    [[product_image]],
                    colWidths=[
                        175 * mm
                    ],
                )

                image_table.setStyle(
                    TableStyle([
                        (
                            "ALIGN",
                            (0, 0),
                            (-1, -1),
                            "CENTER",
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor(
                                "#E2E8F0"
                            ),
                        ),
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            colors.HexColor(
                                "#F8FAFC"
                            ),
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                    ])
                )

                story.append(
                    image_table
                )

            except Exception:
                # Image failure should never
                # stop PDF generation.
                pass

    # ========================================================
    # COMPLIANCE OVERVIEW
    # ========================================================

    story.append(
        Paragraph(
            "Compliance Overview",
            heading_style,
        )
    )

    score = summary[
        "score"
    ]

    if score is None:
        score_text = (
            "Not available"
        )
    else:
        try:
            score_text = (
                f"{float(score):.2f}%"
            )
        except (
            TypeError,
            ValueError,
        ):
            score_text = (
                f"{score}%"
            )

    score_table = Table(
        [[
            Paragraph(
                "<b>COMPLIANCE SCORE</b>",
                center_style,
            ),
            Paragraph(
                f"<b>{safe_text(score_text)}</b>",
                center_style,
            ),
            Paragraph(
                "<b>FINAL STATUS</b>",
                center_style,
            ),
            Paragraph(
                (
                    f"<b>"
                    f"{safe_text(get_status_label(final_status))}"
                    f"</b>"
                ),
                center_style,
            ),
        ]],
        colWidths=[
            42 * mm,
            35 * mm,
            35 * mm,
            63 * mm,
        ],
    )

    score_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, 0),
                colors.HexColor("#F1F5F9"),
            ),
            (
                "BACKGROUND",
                (1, 0),
                (1, 0),
                colors.white,
            ),
            (
                "BACKGROUND",
                (2, 0),
                (2, 0),
                colors.HexColor("#F1F5F9"),
            ),
            (
                "BACKGROUND",
                (3, 0),
                (3, 0),
                get_status_background(
                    final_status
                ),
            ),
            (
                "TEXTCOLOR",
                (3, 0),
                (3, 0),
                get_status_color(
                    final_status
                ),
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.6,
                colors.HexColor("#CBD5E1"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                10,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                10,
            ),
        ])
    )

    story.append(
        score_table
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # ========================================================
    # SUMMARY COUNTS
    # ========================================================

    summary_table = Table(
        [
            [
                "Passed",
                "Failed",
                "Needs Review",
                "Not Checked",
            ],
            [
                str(
                    summary["passed"]
                ),
                str(
                    summary["failed"]
                ),
                str(
                    summary["needs_review"]
                ),
                str(
                    summary["not_checked"]
                ),
            ],
        ],
        colWidths=[
            43.75 * mm,
            43.75 * mm,
            43.75 * mm,
            43.75 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#F1F5F9"),
            ),
            (
                "BACKGROUND",
                (0, 1),
                (0, 1),
                colors.HexColor("#ECFDF3"),
            ),
            (
                "BACKGROUND",
                (1, 1),
                (1, 1),
                colors.HexColor("#FEF2F2"),
            ),
            (
                "BACKGROUND",
                (2, 1),
                (2, 1),
                colors.HexColor("#FFFBEB"),
            ),
            (
                "BACKGROUND",
                (3, 1),
                (3, 1),
                colors.HexColor("#F8FAFC"),
            ),
            (
                "TEXTCOLOR",
                (0, 1),
                (0, 1),
                colors.HexColor("#15803D"),
            ),
            (
                "TEXTCOLOR",
                (1, 1),
                (1, 1),
                colors.HexColor("#DC2626"),
            ),
            (
                "TEXTCOLOR",
                (2, 1),
                (2, 1),
                colors.HexColor("#D97706"),
            ),
            (
                "TEXTCOLOR",
                (3, 1),
                (3, 1),
                colors.HexColor("#64748B"),
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#CBD5E1"),
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
        ])
    )

    story.append(
        summary_table
    )

    # ========================================================
    # PRODUCT INFORMATION
    # ========================================================

    story.append(
        Paragraph(
            "Product Information",
            heading_style,
        )
    )

    food_license = (
        product.get("food_license")
        or product.get("fssai_license")
    )

    product_rows = [
        (
            "Product Name",
            product.get("name"),
        ),
        (
            "Brand",
            product.get("brand"),
        ),
        (
            "Commodity",
            product.get("commodity")
            or product.get(
                "commodity_name"
            ),
        ),
        (
            "Net Quantity",
            product.get(
                "net_quantity"
            ),
        ),
        (
            "MRP",
            product.get("mrp"),
        ),
        (
            "Manufacturer",
            product.get(
                "manufacturer"
            ),
        ),
        (
            "Packaging Date",
            product.get(
                "packaging_date"
            ),
        ),
        (
            "Best Before",
            product.get(
                "best_before"
            ),
        ),
        (
            "FSSAI / Food License",
            food_license,
        ),
    ]

    formatted_product_rows = []

    for label, value in product_rows:

        formatted_product_rows.append(
            [
                Paragraph(
                    (
                        f"<b>"
                        f"{safe_text(label)}"
                        f"</b>"
                    ),
                    normal_style,
                ),
                Paragraph(
                    safe_text(value),
                    normal_style,
                ),
            ]
        )

    product_table = Table(
        formatted_product_rows,
        colWidths=[
            50 * mm,
            125 * mm,
        ],
    )

    product_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#F8FAFC"),
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#E2E8F0"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
        ])
    )

    story.append(
        product_table
    )

    # ========================================================
    # COMPLIANCE CHECKS
    # ========================================================

    if checks:

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "Legal Compliance Checks",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                (
                    "Rule-based verification of "
                    "package declarations and "
                    "available OCR evidence."
                ),
                normal_style,
            )
        )

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        for index, check in enumerate(
            checks,
            start=1,
        ):

            if not isinstance(
                check,
                dict,
            ):
                continue

            field = check.get(
                "field",
                "Unknown",
            )

            rule_number = check.get(
                "rule_number",
                "-",
            )

            status = normalize_status(
                check.get(
                    "status",
                    "NOT_CHECKED",
                )
            )

            description = check.get(
                "description",
                "",
            )

            reason = check.get(
                "reason",
                "",
            )

            confidence = confidence_percent(
                check.get(
                    "confidence",
                    0,
                )
            )

            # ------------------------------------------------
            # CHECK HEADER
            # ------------------------------------------------

            check_header = Table(
                [[
                    Paragraph(
                        (
                            f"<b>{index}. "
                            f"{safe_text(field)}</b>"
                        ),
                        normal_style,
                    ),
                    Paragraph(
                        (
                            f"<b>Rule "
                            f"{safe_text(rule_number)}</b>"
                        ),
                        center_style,
                    ),
                    Paragraph(
                        (
                            f"<b>"
                            f"{safe_text(get_status_label(status))}"
                            f"</b>"
                        ),
                        center_style,
                    ),
                ]],
                colWidths=[
                    90 * mm,
                    30 * mm,
                    55 * mm,
                ],
            )

            check_header.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, 0),
                        colors.HexColor("#F8FAFC"),
                    ),
                    (
                        "BACKGROUND",
                        (2, 0),
                        (2, 0),
                        get_status_background(
                            status
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (2, 0),
                        (2, 0),
                        get_status_color(
                            status
                        ),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#CBD5E1"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ])
            )

            detail_rows = [
                [
                    Paragraph(
                        "<b>Requirement</b>",
                        normal_style,
                    ),
                    Paragraph(
                        safe_text(
                            description,
                            "No description available.",
                        ),
                        normal_style,
                    ),
                ],
            ]

            # ------------------------------------------------
            # FINDING
            # ------------------------------------------------

            if reason:

                detail_rows.append(
                    [
                        Paragraph(
                            "<b>Finding</b>",
                            normal_style,
                        ),
                        Paragraph(
                            safe_text(
                                reason
                            ),
                            normal_style,
                        ),
                    ]
                )

            # ------------------------------------------------
            # DETECTED VALUE
            # ------------------------------------------------

            value = check.get(
                "value"
            )

            if (
                value is not None
                and value != ""
            ):

                detail_rows.append(
                    [
                        Paragraph(
                            "<b>Detected Value</b>",
                            normal_style,
                        ),
                        Paragraph(
                            safe_text(
                                value
                            ),
                            normal_style,
                        ),
                    ]
                )

            # ------------------------------------------------
            # CONFIDENCE
            # ------------------------------------------------

            detail_rows.append(
                [
                    Paragraph(
                        "<b>Confidence</b>",
                        normal_style,
                    ),
                    Paragraph(
                        f"{confidence}%",
                        normal_style,
                    ),
                ]
            )

            # ------------------------------------------------
            # EVIDENCE
            # ------------------------------------------------

            evidence = (
                check.get(
                    "evidence"
                )
                or []
            )

            if evidence:

                evidence_items = []

                if isinstance(
                    evidence,
                    list,
                ):
                    evidence_items = evidence
                else:
                    evidence_items = [
                        evidence
                    ]

                evidence_text = (
                    "<br/>".join(
                        f"• {safe_text(item)}"
                        for item in evidence_items
                    )
                )

                detail_rows.append(
                    [
                        Paragraph(
                            "<b>Evidence</b>",
                            normal_style,
                        ),
                        Paragraph(
                            evidence_text,
                            small_style,
                        ),
                    ]
                )

            # ------------------------------------------------
            # POSSIBLE VALUES
            # ------------------------------------------------

            candidates = (
                check.get(
                    "candidates"
                )
                or check.get(
                    "possible_values"
                )
                or []
            )

            if candidates:

                if not isinstance(
                    candidates,
                    list,
                ):
                    candidates = [
                        candidates
                    ]

                candidate_text = (
                    "<br/>".join(
                        f"• {safe_text(item)}"
                        for item in candidates
                    )
                )

                detail_rows.append(
                    [
                        Paragraph(
                            "<b>Possible Values</b>",
                            normal_style,
                        ),
                        Paragraph(
                            candidate_text,
                            small_style,
                        ),
                    ]
                )

            detail_table = Table(
                detail_rows,
                colWidths=[
                    40 * mm,
                    135 * mm,
                ],
            )

            detail_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor("#FAFBFC"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#E2E8F0"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ])
            )

            story.append(
                KeepTogether([
                    check_header,
                    detail_table,
                    Spacer(
                        1,
                        5 * mm,
                    ),
                ])
            )

    # ========================================================
    # FINAL DECISION
    # ========================================================

    story.append(
        Paragraph(
            "Final Inspection Decision",
            heading_style,
        )
    )

    if final_status == "COMPLIANT":

        decision_text = (
            "The package passed the configured "
            "compliance checks. No failed "
            "requirement was identified by "
            "the PARAKH rule engine."
        )

    elif final_status == "NON_COMPLIANT":

        decision_text = (
            "One or more mandatory compliance "
            "requirements failed validation. "
            "The package should be reviewed "
            "for corrective action."
        )

    elif final_status == "NEEDS_REVIEW":

        decision_text = (
            "One or more declarations require "
            "manual verification. The displayed "
            "result should not be treated as a "
            "final legal determination without "
            "inspector review."
        )

    else:

        decision_text = (
            "The inspection could not be fully "
            "completed with the available "
            "information."
        )

    decision_table = Table(
        [[
            Paragraph(
                (
                    f"<b>"
                    f"{safe_text(get_status_label(final_status))}"
                    f"</b>"
                ),
                center_style,
            ),
            Paragraph(
                safe_text(
                    decision_text
                ),
                normal_style,
            ),
        ]],
        colWidths=[
            45 * mm,
            130 * mm,
        ],
    )

    decision_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, 0),
                get_status_background(
                    final_status
                ),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (0, 0),
                get_status_color(
                    final_status
                ),
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.6,
                colors.HexColor("#CBD5E1"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                10,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                10,
            ),
        ])
    )

    story.append(
        decision_table
    )

    # ========================================================
    # OCR EVIDENCE
    # ========================================================

    ocr_text = (
        analysis_result.get(
            "ocr_text"
        )
        or ""
    )

    if ocr_text:

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "OCR Evidence",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                (
                    "Raw text extracted from the "
                    "uploaded package image. This "
                    "section is provided as inspection "
                    "evidence and may contain OCR "
                    "ambiguity."
                ),
                normal_style,
            )
        )

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        for line in str(
            ocr_text
        ).splitlines():

            line = line.strip()

            if not line:
                continue

            story.append(
                Paragraph(
                    safe_text(line),
                    small_style,
                )
            )

            story.append(
                Spacer(
                    1,
                    1.5 * mm,
                )
            )

    # ========================================================
    # DISCLAIMER
    # ========================================================

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    disclaimer_text = (
        "<b>Inspector Note:</b> "
        "PARAKH provides AI-assisted OCR, "
        "information extraction and "
        "rule-based verification. Any "
        "<b>NEEDS REVIEW</b> result requires "
        "manual verification before a final "
        "regulatory decision is made."
    )

    disclaimer = Table(
        [[
            Paragraph(
                disclaimer_text,
                small_style,
            )
        ]],
        colWidths=[
            175 * mm
        ],
    )

    disclaimer.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.HexColor("#F8FAFC"),
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#CBD5E1"),
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                9,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                9,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),
        ])
    )

    story.append(
        disclaimer
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "report_id": report_id,
        "filename": filename,
        "path": str(output_path),
    }