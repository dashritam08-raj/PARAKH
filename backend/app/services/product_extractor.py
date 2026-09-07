import re


# ============================================================
# PARAKH - PRODUCT FIELD EXTRACTOR
# ============================================================


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(text: str) -> str:

    if not text:
        return ""

    text = text.replace(
        "\r",
        "\n"
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n+",
        "\n",
        text
    )

    return text.strip()


def normalize_spaces(text: str) -> str:

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def find_first(
    patterns,
    text,
    flags=re.IGNORECASE
):

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags
        )

        if match and match.lastindex:

            return match.group(
                1
            ).strip()

    return None


def is_reasonable_text(value):

    if not value:
        return False

    value = normalize_spaces(
        value
    )

    if len(value) < 2:
        return False

    # Reject obvious Hindi OCR garbage
    if re.search(
        r"[\u0900-\u097F]",
        value
    ):
        return False

    alphanumeric = len(
        re.findall(
            r"[A-Za-z0-9]",
            value
        )
    )

    if alphanumeric < 3:
        return False

    return True


# ============================================================
# PRODUCT NAME
# ============================================================

def extract_product_name(text):

    # Strong known product phrases
    strong_patterns = [

        # Preserve the full product name when OCR sees it.
        r"\b(Danish\s+Butter\s+Cookies)\b",

        r"\b(Premium\s+Butter\s+Cookies)\b",

        r"\b(Butter\s+Cookies)\b",

        r"\b(Butter\s+Cookie)\b",
    ]

    for pattern in strong_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return normalize_spaces(
                match.group(1)
            )

    # OCR may separate the words
    # Butter
    # ...
    # Cookies

    butter_match = re.search(
        r"\bButter\b",
        text,
        re.IGNORECASE
    )

    cookies_match = re.search(
        r"\bCookies\b",
        text,
        re.IGNORECASE
    )

    if butter_match and cookies_match:

        return "Butter Cookies"

    # Generic fallback
    generic_patterns = [

        r"\b([A-Za-z]{2,30}\s+Cookies)\b",

        r"\b([A-Za-z]{2,30}\s+Biscuits)\b",
    ]

    for pattern in generic_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = normalize_spaces(
                match.group(1)
            )

            if is_reasonable_text(
                value
            ):

                return value

    return None


# ============================================================
# BRAND
# ============================================================

def extract_brand(text):

    text_lower = text.lower()

    if "cremica" in text_lower:

        return "Cremica"

    # Brand printed prominently on Danish Butter Cookies packs.
    if re.search(r"\bDanish\b", text, re.IGNORECASE):

        return "Danish"

    if (
        "mrs. bector" in text_lower
        or
        "mrs bector" in text_lower
    ):

        return "Mrs. Bector's"

    if "bector" in text_lower:

        return "Bector's"

    return None


# ============================================================
# COMMODITY
# ============================================================

def extract_commodity_name(text):

    patterns = [

        r"Commodity\s+Name\s*:\s*"
        r"([A-Za-z][A-Za-z\s]+)",

        r"Commodity\s+Name\s*[-:]\s*"
        r"([A-Za-z][A-Za-z\s]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = normalize_spaces(
                match.group(1)
            )

            value = re.split(
                r"(?:INGREDIENTS|NUTRITIONAL|MRP|NET)",
                value,
                flags=re.IGNORECASE
            )[0].strip()

            if value:

                return value.upper()

    if re.search(
        r"\bBISCUITS\b",
        text,
        re.IGNORECASE
    ):

        return "BISCUITS"

    if re.search(
        r"\bBISCUIT\b",
        text,
        re.IGNORECASE
    ):

        return "BISCUITS"

    return None


# ============================================================
# NET QUANTITY
# ============================================================

def extract_net_quantity(text):

    quantity_pattern = (
        r"[0-9]+(?:\.[0-9]+)?\s*"
        r"(?:kg|g|gm|grams?|ml|l|litres?|liters?)"
    )

    # Prefer the explicit package label. OCR may place the value later
    # because the package has multiple columns, so collect candidates
    # after the label and use the last candidate before another major
    # declaration. This avoids selecting nutrition serving values.
    label_match = re.search(
        r"\bNET\s*(?:WEIGHT|WT\.?|QUANTITY|QTY\.?)\b",
        text,
        re.IGNORECASE
    )

    if label_match:

        remainder = text[label_match.end():]

        # Keep the search local to the declaration area.
        stop_match = re.search(
            r"\b(?:MFG\.?\s*DATE|MANUFACTUR(?:E|ING|ED)\s+DATE|"
            r"BEST\s+BEFORE|INGREDIENTS|NUTRITIONAL)\b",
            remainder,
            re.IGNORECASE
        )

        if stop_match:
            remainder = remainder[:stop_match.start()]
        else:
            remainder = remainder[:350]

        candidates = re.findall(
            quantity_pattern,
            remainder,
            re.IGNORECASE
        )

        if candidates:

            return normalize_spaces(
                candidates[-1]
            )

    # Conservative fallback when no explicit net-quantity label exists.
    # Do not hard-code 100g: it is commonly a nutrition serving value.
    matches = re.findall(
        r"\b(" + quantity_pattern + r")\b",
        text,
        re.IGNORECASE
    )

    if matches:

        return normalize_spaces(
            matches[0]
        )

    return None


# ============================================================
# MRP
# ============================================================

def extract_mrp(text):

    # First handle OCR where the amount appears on a later line,
    # e.g. MRP: ... 250.00. Prefer a decimal/currency amount so
    # nearby values such as 500g are not mistaken for MRP.
    label_patterns = [
        r"\bM\.?\s*R\.?\s*P\.?\s*[:\-]?\s*"
        r".{0,160}?"
        r"(?:Rs\.?|INR|₹)?\s*"
        r"([0-9]{1,7}[.,][0-9]{1,2})\b",

        r"\bM\.?\s*R\.?\s*P\.?\s*[:\-]?\s*"
        r".{0,160}?"
        r"(?:Rs\.?|INR|₹)\s*"
        r"([0-9]{1,7}(?:[.,][0-9]{1,2})?)\b",

        r"\bM\.?\s*R\.?\s*P\.?\s*[:\-]?\s*"
        r"(?:Rs\.?|INR|₹)?\s*"
        r"([0-9]{1,7}(?:[.,][0-9]{1,2})?)\b",
    ]

    for pattern in label_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        if not match:
            continue

        value = match.group(1).replace(",", ".")

        try:
            number = float(value)
        except ValueError:
            continue

        if number >= 1:
            return f"₹{number:.2f}"

    # Fallback for formats such as 250.00 Rs.
    fallback_patterns = [
        r"\b([0-9]{1,7}(?:[.,][0-9]{1,2})?)\s*(?:Rs\.?|INR|₹)\b?",
    ]

    for pattern in fallback_patterns:

        for match in re.finditer(pattern, text, re.IGNORECASE):

            value = match.group(1).replace(",", ".")

            try:
                number = float(value)
            except ValueError:
                continue

            if number >= 1:
                return f"₹{number:.2f}"

    return None


# ============================================================
# UNIT SALE PRICE
# ============================================================

def extract_unit_sale_price(text):

    patterns = [

        r"(?:Rs\.?|₹)\s*"
        r"([0-9]+(?:\.[0-9]{1,2})?)"
        r"\s*PER\s*"
        r"(g|kg|ml|l|cm|m|number|unit)",

        r"([0-9]+(?:\.[0-9]{1,2})?)"
        r"\s*PER\s*"
        r"(g|kg|ml|l|cm|m|number|unit)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            price = match.group(
                1
            )

            unit = match.group(
                2
            ).lower()

            return (
                f"₹{price} per {unit}"
            )

    return None


# ============================================================
# MANUFACTURER
# ============================================================

def extract_manufacturer(text):

    # ------------------------------------------------------------
    # Label-aware manufacturer extraction.
    # Handles common package labels such as:
    #   MANUFACTURED & PACKED BY: Danish Foods Pvt. Ltd.
    #   MANUFACTURED AND PACKED BY: Company Name
    #   MANUFACTURED BY: Company Name
    #   PACKED BY: Company Name
    #
    # OCR may place ingredient text before the company name on the
    # same line. Therefore, do NOT reject the complete line merely
    # because it contains words such as "sugar" or "salt".
    # ------------------------------------------------------------
    label_patterns = [
        r"MANUFACTURED\s*&\s*PACKED\s+BY",
        r"MANUFACTURED\s+AND\s+PACKED\s+BY",
        r"MANUFACTURED\s+BY",
        r"MANUFACTURED\s+AND\s+MARKETED\s+BY",
        r"PACKED\s+BY",
    ]

    company_suffix = (
        r"PVT\.?\s*LTD\.?|"
        r"PRIVATE\s+LIMITED|"
        r"LIMITED|"
        r"LTD\.?|"
        r"LLP|"
        r"INC\.?|"
        r"CORPORATION|"
        r"CORP\.?|"
        r"COMPANY|"
        r"CO\.?"
    )

    for label_pattern in label_patterns:

        label_matches = list(
            re.finditer(
                label_pattern,
                text,
                re.IGNORECASE
            )
        )

        for label_match in label_matches:

            remainder = text[label_match.end():]
            remainder = re.sub(
                r"^[\s:;,.\-]+",
                "",
                remainder
            )

            # Keep the OCR window local to the manufacturer label.
            window = remainder[:500]

            # ----------------------------------------------------
            # 1. Strong company-name match.
            #
            # Example OCR:
            #   Invert Sugar Syrup, Salt, Raising Agents ...,
            #   Danish Foods Pvt. Ltd.
            #
            # Capture the company name immediately before a
            # corporate suffix instead of taking the whole OCR line.
            # ----------------------------------------------------
            company_patterns = [
                rf"\b([A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*){{0,4}}\s+(?:{company_suffix}))\b",
                rf"\b([A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*){{0,4}}\s+(?:{company_suffix}))\b",
            ]

            for company_pattern in company_patterns:

                company_matches = re.finditer(
                    company_pattern,
                    window,
                    re.IGNORECASE
                )

                for company_match in company_matches:

                    value = normalize_spaces(
                        company_match.group(1)
                    ).strip(" :-,.")

                    if not value:
                        continue

                    # Never accept obvious ingredient fragments as
                    # the manufacturer.
                    if re.search(
                        r"\b(?:invert\s+sugar|sugar|salt|raising\s+agents|"
                        r"wheat\s+flour|butter|ingredients?|emulsifier|"
                        r"artificial\s+flavour|nutrition(?:al)?)\b",
                        value,
                        re.IGNORECASE
                    ):
                        # If the match contains ingredient text but
                        # ends in a company suffix, take the last
                        # few words before the suffix.
                        words = value.split()
                        suffix_index = None

                        for index, word in enumerate(words):
                            if re.fullmatch(
                                company_suffix,
                                word,
                                re.IGNORECASE
                            ):
                                suffix_index = index
                                break

                        if suffix_index is not None:
                            candidate_words = words[
                                max(0, suffix_index - 3):
                                suffix_index + 1
                            ]
                            value = " ".join(candidate_words).strip(" :-,.")

                    if (
                        is_reasonable_text(value)
                        and not re.search(
                            r"\b(?:invert\s+sugar|sugar|salt|raising\s+agents|"
                            r"wheat\s+flour|butter|ingredients?|emulsifier)\b",
                            value,
                            re.IGNORECASE
                        )
                    ):
                        return value

            # ----------------------------------------------------
            # 2. Line-based fallback for labels where OCR keeps the
            # company name cleanly on the next line.
            # ----------------------------------------------------
            lines = [
                normalize_spaces(line)
                for line in re.split(r"[\r\n]+", window)
                if normalize_spaces(line)
            ]

            for line in lines[:5]:

                value = re.split(
                    r"(?:MRP|NET\s+(?:WEIGHT|QUANTITY)|PKD|LOT|"
                    r"BEST\s+BEFORE|MFG\.?\s*DATE|"
                    r"LIC\.?\s*NO|INGREDIENTS|NUTRITIONAL|"
                    r"NET\s*WT)",
                    line,
                    flags=re.IGNORECASE
                )[0].strip(" :-")

                if not value:
                    continue

                if re.search(
                    r"\b(?:invert\s+sugar|sugar|salt|raising\s+agents|"
                    r"wheat\s+flour|butter|ingredients?|emulsifier|"
                    r"artificial\s+flavour|nutrition(?:al)?)\b",
                    value,
                    re.IGNORECASE
                ):
                    continue

                if (
                    re.search(
                        rf"\b(?:{company_suffix})\b",
                        value,
                        re.IGNORECASE
                    )
                    and is_reasonable_text(value)
                ):
                    return value

                if (
                    is_reasonable_text(value)
                    and not re.search(
                        r"\b(?:invert\s+sugar|sugar|salt|raising\s+agents|"
                        r"wheat\s+flour|butter|ingredients?)\b",
                        value,
                        re.IGNORECASE
                    )
                ):
                    # Only use a non-company fallback when it looks
                    # like a plausible named business.
                    if len(value.split()) <= 8:
                        return value

    # Known manufacturer fallback.
    known_company = re.search(
        r"MRS\.?\s*BECTORS?\s+"
        r"FOOD\s+SPECIALITIES(?:\s+LTD\.?)?",
        text,
        re.IGNORECASE
    )

    if known_company:
        return normalize_spaces(known_company.group(0))

    return None


# ============================================================
# PACKAGING DATE
# ============================================================

def extract_packaging_date(text):

    patterns = [

        # PKD / P.K.D / PACKED DATE
        r"\bPKD\.?\s*"
        r"[,.:\-]?\s*"
        r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",

        r"\bP\.?K\.?D\.?\s*"
        r"[,.:\-]?\s*"
        r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",

        r"\bPACKED\s*(?:ON|DATE)?\s*"
        r"[:\-]?\s*"
        r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",

        # Common packaged-food label: MFG. DATE: 15/01/2024
        r"\bM\.?\s*F\.?\s*G\.?\s*(?:DATE|DT)?\s*"
        r"[:\-]?\s*"
        r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",

        r"\bMANUFACT(?:URE|URING|URED)\s*"
        r"(?:DATE|DT)?\s*"
        r"[:\-]?\s*"
        r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return match.group(1)

    return None


# ============================================================
# BEST BEFORE
# ============================================================

def extract_best_before(text):

    patterns = [

        # Actual date: BEST BEFORE: 14/07/2024
        r"BEST\s+BEFORE\s*"
        r"[:\-]?\s*"
        r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",

        # Duration: BEST BEFORE 6 MONTHS
        r"BEST\s+BEFORE\s*"
        r"[:\-]?\s*"
        r"(\d+\s+(?:MONTHS?|DAYS?|YEARS?))",
    ]

    value = find_first(
        patterns,
        text
    )

    if value:

        return normalize_spaces(
            value
        )

    return None


# ============================================================
# PHONE CANDIDATES
# ============================================================

def find_phone_candidates(text):

    patterns = [

        # 1-800-1802065
        r"\b\d{1,4}-\d{3}-\d{6,7}\b",

        # 1800-1802065
        r"\b\d{4}-\d{6,7}\b",

        # 1 800 1802065
        r"\b\d{1,4}\s+\d{3}\s+\d{6,7}\b",
    ]

    candidates = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text
        )

        for value in matches:

            value = normalize_spaces(
                value
            )

            value = value.replace(
                " ",
                "-"
            )

            if value not in candidates:

                candidates.append(
                    value
                )

    return candidates


# ============================================================
# CUSTOMER CONTACT
# ============================================================

def extract_customer_contact(text):

    # --------------------------------------------------------
    # First: explicit Toll Free
    # --------------------------------------------------------

    toll_free_match = re.search(
        r"("
        r"\d{1,4}[-\s]\d{3}[-\s]\d{6,7}"
        r")"
        r"\s*"
        r"\(?\s*Toll\s*Free\s*\)?",
        text,
        re.IGNORECASE
    )

    if toll_free_match:

        return normalize_spaces(
            toll_free_match.group(1)
        ).replace(
            " ",
            "-"
        )


    # --------------------------------------------------------
    # Explicit phone label
    # --------------------------------------------------------

    phone_match = re.search(
        r"(?:Ph\.?|Phone|Tel\.?|"
        r"Telephone)"
        r"\s*[:\-]?\s*"
        r"("
        r"\d{1,4}[-\s]\d{3}[-\s]\d{6,7}"
        r")",
        text,
        re.IGNORECASE
    )

    if phone_match:

        return normalize_spaces(
            phone_match.group(1)
        ).replace(
            " ",
            "-"
        )


    # --------------------------------------------------------
    # Indian mobile fallback
    # --------------------------------------------------------

    mobile_match = re.search(
        r"\b([6-9]\d{9})\b",
        text
    )

    if mobile_match:

        return mobile_match.group(
            1
        )


    # IMPORTANT:
    # Never select random OCR numbers.

    return None


# ============================================================
# FOOD LICENCE / FSSAI
# ============================================================

def extract_food_license(text):

    patterns = [

        r"(?:Lic\.?\s*No\.?|"
        r"License\s*No\.?|"
        r"FSSAI)"
        r"[^\d]*"
        r"(\d{10,14})",
    ]

    value = find_first(
        patterns,
        text,
        re.IGNORECASE
    )

    if value:

        return value

    return None


# ============================================================
# CONFIDENCE + EVIDENCE
# ============================================================

def build_field_result(
    value=None,
    confidence=0.0,
    status="NOT_DETECTED",
    evidence=None,
    candidates=None
):

    return {

        "value":
            value,

        "confidence":
            round(
                confidence,
                2
            ),

        "status":
            status,

        "evidence":
            evidence or [],

        "candidates":
            candidates or []
    }


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract_product_fields(text):

    if not text:

        return {

            "product_name": None,

            "brand": None,

            "commodity_name": None,

            "net_quantity": None,

            "mrp": None,

            "unit_sale_price": None,

            "manufacturer": None,

            "packaging_date": None,

            "best_before": None,

            "consumer_complaint_contact":
                build_field_result(),

            "food_license": None,
        }


    normalized_text = clean_text(
        text
    )


    # ========================================================
    # STANDARD FIELDS
    # ========================================================

    product_name = extract_product_name(
        normalized_text
    )

    brand = extract_brand(
        normalized_text
    )

    commodity_name = extract_commodity_name(
        normalized_text
    )

    net_quantity = extract_net_quantity(
        normalized_text
    )

    mrp = extract_mrp(
        normalized_text
    )

    unit_sale_price = extract_unit_sale_price(
        normalized_text
    )

    manufacturer = extract_manufacturer(
        normalized_text
    )

    packaging_date = extract_packaging_date(
        normalized_text
    )

    best_before = extract_best_before(
        normalized_text
    )

    food_license = extract_food_license(
        normalized_text
    )


    # ========================================================
    # CUSTOMER CONTACT WITH CONFIDENCE
    # ========================================================

    phone_candidates = find_phone_candidates(
        normalized_text
    )


    consumer_contact = None

    consumer_contact_confidence = 0.0

    consumer_contact_status = (
        "NOT_DETECTED"
    )


    # --------------------------------------------------------
    # Exactly one candidate
    # --------------------------------------------------------

    if len(phone_candidates) == 1:

        consumer_contact = (
            phone_candidates[0]
        )

        consumer_contact_confidence = 0.95

        consumer_contact_status = (
            "DETECTED"
        )


    # --------------------------------------------------------
    # Multiple candidates
    # --------------------------------------------------------

    elif len(phone_candidates) > 1:

        # DO NOT GUESS.

        consumer_contact = None

        consumer_contact_confidence = 0.60

        consumer_contact_status = (
            "NEEDS_REVIEW"
        )


    # --------------------------------------------------------
    # No formatted toll-free candidate
    # --------------------------------------------------------

    else:

        fallback_contact = (
            extract_customer_contact(
                normalized_text
            )
        )

        if fallback_contact:

            consumer_contact = (
                fallback_contact
            )

            consumer_contact_confidence = (
                0.80
            )

            consumer_contact_status = (
                "DETECTED"
            )


    # ========================================================
    # RESULT
    # ========================================================

    return {

        "product_name":
            product_name,

        "brand":
            brand,

        "commodity_name":
            commodity_name,

        "net_quantity":
            net_quantity,

        "mrp":
            mrp,

        "unit_sale_price":
            unit_sale_price,

        "manufacturer":
            manufacturer,

        "packaging_date":
            packaging_date,

        "best_before":
            best_before,

        "consumer_complaint_contact":
            build_field_result(

                value=consumer_contact,

                confidence=(
                    consumer_contact_confidence
                ),

                status=(
                    consumer_contact_status
                ),

                evidence=(
                    phone_candidates
                ),

                candidates=(
                    phone_candidates
                )
            ),

        "food_license":
            food_license,
    }