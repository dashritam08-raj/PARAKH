import re


# ============================================================
# PARAKH - COMPLIANCE ENGINE
# ============================================================
#
# Converts extracted product information into
# rule-based compliance results.
#
# Status values:
#
#   PASS
#   FAIL
#   NEEDS_REVIEW
#   NOT_CHECKED
#
# IMPORTANT:
# Missing OCR evidence is not automatically treated as
# a legal violation. It is marked NEEDS_REVIEW when
# the declaration is mandatory.
#
# ============================================================


# ============================================================
# HELPERS
# ============================================================

def has_value(value):

    if value is None:
        return False

    if isinstance(value, dict):

        value = value.get(
            "value"
        )

    if value is None:
        return False

    return bool(
        str(value).strip()
    )


def normalize_text(value):

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


# ============================================================
# NET QUANTITY VALIDATION
# ============================================================

def validate_net_quantity(value):

    if not has_value(value):

        return {

            "status": "NEEDS_REVIEW",

            "reason":
                "Net quantity was not detected."
        }


    value = normalize_text(
        value
    )


    # Examples:
    # 100g
    # 500 g
    # 1kg
    # 250ml
    # 1 litre

    pattern = (
        r"^\d+(?:\.\d+)?\s*"
        r"(kg|g|gm|grams?|ml|l|litres?|liters?)$"
    )


    if re.fullmatch(
        pattern,
        value,
        re.IGNORECASE
    ):

        return {

            "status": "PASS",

            "reason":
                "Net quantity is declared "
                "in a recognizable unit."
        }


    return {

        "status": "FAIL",

        "reason":
            "Net quantity format could not "
            "be validated."
    }


# ============================================================
# MRP VALIDATION
# ============================================================

def validate_mrp(value):

    if not has_value(value):

        return {

            "status": "NEEDS_REVIEW",

            "reason":
                "Retail sale price was not detected."
        }


    value = normalize_text(
        value
    )


    patterns = [

        r"^₹\s*\d+(?:\.\d{1,2})?$",

        r"^Rs\.?\s*\d+(?:\.\d{1,2})?$",

        r"^\d+(?:\.\d{1,2})?\s*(?:Rs\.?)?$",
    ]


    for pattern in patterns:

        if re.fullmatch(
            pattern,
            value,
            re.IGNORECASE
        ):

            return {

                "status": "PASS",

                "reason":
                    "Retail sale price is "
                    "present in a recognizable "
                    "currency format."
            }


    return {

        "status": "FAIL",

        "reason":
            "Retail sale price format "
            "could not be validated."
    }


# ============================================================
# UNIT SALE PRICE VALIDATION
# ============================================================

def validate_unit_sale_price(
    value,
    net_quantity=None
):

    if not has_value(value):

        return {

            "status": "NEEDS_REVIEW",

            "reason":
                "Unit sale price was not detected."
        }


    value = normalize_text(
        value
    )


    pattern = (
        r"^₹\s*\d+(?:\.\d{1,2})?\s+"
        r"per\s+"
        r"(g|kg|ml|l|cm|m|number|unit)$"
    )


    if re.fullmatch(
        pattern,
        value,
        re.IGNORECASE
    ):

        return {

            "status": "PASS",

            "reason":
                "Unit sale price has a "
                "recognizable unit-price format."
        }


    return {

        "status": "FAIL",

        "reason":
            "Unit sale price format "
            "could not be validated."
    }


# ============================================================
# PACKAGING DATE VALIDATION
# ============================================================

def validate_packaging_date(
    value
):

    if not has_value(value):

        return {

            "status": "NEEDS_REVIEW",

            "reason":
                "Packaging/manufacturing date "
                "was not detected."
        }


    value = normalize_text(
        value
    )


    pattern = (
        r"^\d{1,2}[./-]"
        r"\d{1,2}[./-]"
        r"\d{2,4}$"
    )


    if re.fullmatch(
        pattern,
        value
    ):

        return {

            "status": "PASS",

            "reason":
                "Packaging date has a "
                "recognizable date format."
        }


    return {

        "status": "FAIL",

        "reason":
            "Packaging date format "
            "could not be validated."
    }


# ============================================================
# CONSUMER CONTACT VALIDATION
# ============================================================

def validate_consumer_contact(
    value,
    confidence_metadata=None
):

    # --------------------------------------------------------
    # Confidence metadata takes priority.
    # --------------------------------------------------------

    if confidence_metadata:

        metadata_status = (
            confidence_metadata.get(
                "status"
            )
        )


        if metadata_status == (
            "NEEDS_REVIEW"
        ):

            candidates = (
                confidence_metadata.get(
                    "candidates",
                    []
                )
            )


            return {

                "status":
                    "NEEDS_REVIEW",

                "reason":
                    (
                        "Multiple conflicting "
                        "contact-number candidates "
                        "were detected."
                    ),

                "candidates":
                    candidates
            }


    # --------------------------------------------------------
    # No value
    # --------------------------------------------------------

    if not has_value(value):

        return {

            "status":
                "NEEDS_REVIEW",

            "reason":
                (
                    "Consumer complaint contact "
                    "could not be reliably detected."
                )
        }


    value = normalize_text(
        value
    )


    # Toll-free format
    toll_free = re.fullmatch(
        r"\d{1,4}-\d{3}-\d{6,7}",
        value
    )


    # Indian mobile
    mobile = re.fullmatch(
        r"[6-9]\d{9}",
        value
    )


    if toll_free or mobile:

        return {

            "status":
                "PASS",

            "reason":
                (
                    "Consumer complaint "
                    "telephone number has a "
                    "recognizable format."
                )
        }


    return {

        "status":
            "FAIL",

        "reason":
            (
                "Consumer complaint contact "
                "format could not be validated."
            )
    }


# ============================================================
# GENERIC REQUIRED FIELD VALIDATION
# ============================================================

def validate_required_field(
    value,
    field_name
):

    if has_value(value):

        return {

            "status": "PASS",

            "reason":
                f"{field_name} was detected."
        }


    return {

        "status":
            "NEEDS_REVIEW",

        "reason":
            f"{field_name} was not reliably detected."
    }


# ============================================================
# FIELD VALIDATOR
# ============================================================

def is_requirement_applicable(
    requirement,
    product_fields=None
):
    """
    Supports product-specific applicability.

    Requirements are applicable by default for backward
    compatibility. A rule can explicitly exclude a field with
    applicable=false or applicability=not_applicable.

    A future product/category classifier can also provide:
    product_fields["not_applicable_fields"] = [...]
    """
    if requirement.get("applicable") is False:
        return False

    applicability = str(
        requirement.get("applicability", "")
    ).strip().lower()

    if applicability in {
        "not_applicable",
        "not applicable",
        "n/a",
        "na",
    }:
        return False

    product_fields = product_fields or {}

    excluded_fields = product_fields.get(
        "not_applicable_fields",
        []
    )

    if (
        isinstance(excluded_fields, (list, tuple, set))
        and requirement.get("field") in excluded_fields
    ):
        return False

    return True


def validate_requirement(

    requirement,
    product_fields,
    confidence_data
):

    field = requirement.get(
        "field"
    )


    mandatory = requirement.get(
        "mandatory",
        False
    )


    value = product_fields.get(
        field
    )

    # Defensive aliases keep the engine compatible with
    # extractor-friendly names and legal-rule field names.
    if not has_value(value):
        aliases = {
            "retail_sale_price": "mrp",
            "manufacture_or_prepack_date": "packaging_date",
            "manufacturer_or_packer_or_importer": "manufacturer",
        }
        alias_field = aliases.get(field)
        if alias_field:
            value = product_fields.get(alias_field)


    metadata = confidence_data.get(
        field
    )


    # ========================================================
    # CONFIDENCE CHECK
    # ========================================================

    if metadata:

        metadata_status = metadata.get(
            "status"
        )


        if metadata_status == (
            "NEEDS_REVIEW"
        ):

            result = {

                "status":
                    "NEEDS_REVIEW",

                "reason":
                    (
                        "OCR evidence is "
                        "ambiguous."
                    ),

                "confidence":
                    metadata.get(
                        "confidence",
                        0.0
                    ),

                "evidence":
                    metadata.get(
                        "evidence",
                        []
                    ),

                "candidates":
                    metadata.get(
                        "candidates",
                        []
                    )
            }


            return result


    # ========================================================
    # OPTIONAL FIELD
    # ========================================================

    if not mandatory:

        if not has_value(value):

            return {

                "status":
                    "NOT_CHECKED",

                "reason":
                    (
                        "Optional declaration "
                        "was not detected."
                    )
            }


    # ========================================================
    # FIELD-SPECIFIC VALIDATION
    # ========================================================

    if field == "net_quantity":

        return validate_net_quantity(
            value
        )


    if field == "retail_sale_price":

        return validate_mrp(
            value
        )


    if field == "manufacture_or_prepack_date":

        return validate_packaging_date(
            value
        )


    if field == "consumer_complaint_contact":

        return validate_consumer_contact(
            value,
            metadata
        )


    if field == "unit_sale_price":

        return validate_unit_sale_price(
            value,
            product_fields.get(
                "net_quantity"
            )
        )


    # ========================================================
    # GENERIC
    # ========================================================

    return validate_required_field(
        value,
        field
    )


# ============================================================
# BUILD COMPLIANCE CHECKS
# ============================================================

def evaluate_rules(
    legal_rules,
    product_fields,
    confidence_data=None
):

    if confidence_data is None:

        confidence_data = {}


    checks = []


    rules = legal_rules.get(
        "rules",
        []
    )


    for rule in rules:

        rule_number = rule.get(
            "rule_number"
        )


        rule_title = rule.get(
            "title"
        )


        for requirement in rule.get(
            "requirements",
            []
        ):

            field = requirement.get(
                "field"
            )


            if is_requirement_applicable(
                requirement,
                product_fields
            ):
                result = validate_requirement(
                    requirement,
                    product_fields,
                    confidence_data
                )
            else:
                result = {
                    "status": "NOT_APPLICABLE",
                    "reason": (
                        "This declaration is not applicable "
                        "to the current product."
                    )
                }


            check = {

                "rule_id":
                    requirement.get(
                        "id"
                    ),

                "rule_number":
                    rule_number,

                "rule_title":
                    rule_title,

                "field":
                    field,

                "description":
                    requirement.get(
                        "description"
                    ),

                "mandatory":
                    requirement.get(
                        "mandatory",
                        False
                    ),

                "applicability":
                    requirement.get(
                        "applicability",
                        "general"
                    ),

                "value":
                    (
                        product_fields.get(field)
                        if has_value(product_fields.get(field))
                        else product_fields.get(
                            {
                                "retail_sale_price": "mrp",
                                "manufacture_or_prepack_date": "packaging_date",
                                "manufacturer_or_packer_or_importer": "manufacturer",
                            }.get(field)
                        )
                    ),

                "status":
                    result.get(
                        "status"
                    ),

                "reason":
                    result.get(
                        "reason"
                    )
            }


            # ------------------------------------------------
            # Attach confidence/evidence
            # ------------------------------------------------

            metadata = confidence_data.get(
                field
            )

            if not metadata:
                alias_field = {
                    "retail_sale_price": "mrp",
                    "manufacture_or_prepack_date": "packaging_date",
                    "manufacturer_or_packer_or_importer": "manufacturer",
                }.get(field)

                if alias_field:
                    metadata = confidence_data.get(
                        alias_field
                    )


            if metadata:

                check[
                    "confidence"
                ] = metadata.get(
                    "confidence",
                    0.0
                )


                check[
                    "evidence"
                ] = metadata.get(
                    "evidence",
                    []
                )


                check[
                    "candidates"
                ] = metadata.get(
                    "candidates",
                    []
                )


            elif has_value(
                product_fields.get(
                    field
                )
            ):

                check[
                    "confidence"
                ] = 0.95


            else:

                check[
                    "confidence"
                ] = 0.0


            checks.append(
                check
            )


    return checks


# ============================================================
# COMPLIANCE SCORE
# ============================================================

def calculate_compliance_score(
    checks
):

    mandatory_checks = [

        check

        for check in checks

        if check.get(
            "mandatory",
            False
        )
    ]


    if not mandatory_checks:

        return {

            "score":
                None,

            "status":
                "PENDING",

            "passed":
                0,

            "failed":
                0,

            "needs_review":
                0,

            "not_applicable":
                0,

            "total_mandatory":
                0,

            "applicable_mandatory":
                0
        }


    passed = sum(

        1

        for check in mandatory_checks

        if check.get(
            "status"
        ) == "PASS"
    )


    failed = sum(

        1

        for check in mandatory_checks

        if check.get(
            "status"
        ) == "FAIL"
    )


    needs_review = sum(

        1

        for check in mandatory_checks

        if check.get(
            "status"
        ) == "NEEDS_REVIEW"
    )


    total = len(
        mandatory_checks
    )

    # --------------------------------------------------------
    # PRODUCT-SPECIFIC SCORE
    # --------------------------------------------------------
    # PASS contributes to the score.
    # FAIL and NEEDS_REVIEW remain in the denominator.
    # NOT_APPLICABLE is excluded.
    not_applicable = sum(
        1
        for check in mandatory_checks
        if check.get("status") == "NOT_APPLICABLE"
    )

    applicable_mandatory = total - not_applicable

    if applicable_mandatory == 0:
        score = None
    else:
        score = round(
            (passed / applicable_mandatory) * 100,
            2
        )


    # ========================================================
    # FINAL STATUS
    # ========================================================

    if failed > 0:

        overall_status = (
            "NON_COMPLIANT"
        )


    elif needs_review > 0:

        overall_status = (
            "NEEDS_REVIEW"
        )


    elif passed == total:

        overall_status = (
            "COMPLIANT"
        )


    else:

        overall_status = (
            "PENDING"
        )


    return {

        "score":
            score,

        "status":
            overall_status,

        "passed":
            passed,

        "failed":
            failed,

        "needs_review":
            needs_review,

        "not_applicable":
            not_applicable,

        "total_mandatory":
            total,

        "applicable_mandatory":
            applicable_mandatory,

        "score_basis":
            "PASS/applicable mandatory checks; FAIL and NEEDS_REVIEW remain in the denominator; NOT_APPLICABLE is excluded."
    }


# ============================================================
# FINAL EVALUATION
# ============================================================

def evaluate_compliance(
    legal_rules,
    product_fields,
    confidence_data=None
):

    checks = evaluate_rules(

        legal_rules,

        product_fields,

        confidence_data
    )


    scoring = calculate_compliance_score(
        checks
    )


    optional_not_checked = sum(

        1

        for check in checks

        if (
            not check.get(
                "mandatory",
                False
            )
            and
            check.get(
                "status"
            ) == "NOT_CHECKED"
        )
    )


    return {

        "checks":
            checks,

        "summary": {

            "total_checks":
                len(checks),

            "passed":
                sum(
                    1
                    for check in checks
                    if check.get(
                        "status"
                    ) == "PASS"
                ),

            "failed":
                sum(
                    1
                    for check in checks
                    if check.get(
                        "status"
                    ) == "FAIL"
                ),

            "needs_review":
                sum(
                    1
                    for check in checks
                    if check.get(
                        "status"
                    ) == "NEEDS_REVIEW"
                ),

            "not_checked":
                sum(
                    1
                    for check in checks
                    if check.get(
                        "status"
                    ) == "NOT_CHECKED"
                ),

            "optional_not_checked":
                optional_not_checked,

            "mandatory_passed":
                scoring.get(
                    "passed"
                ),

            "mandatory_failed":
                scoring.get(
                    "failed"
                ),

            "mandatory_needs_review":
                scoring.get(
                    "needs_review"
                ),

            "mandatory_not_applicable":
                scoring.get(
                    "not_applicable",
                    0
                ),

            "total_mandatory":
                scoring.get(
                    "total_mandatory"
                ),

            "applicable_mandatory":
                scoring.get(
                    "applicable_mandatory"
                ),

            "compliance_score":
                scoring.get(
                    "score"
                ),

            "overall_status":
                scoring.get(
                    "status"
                )
        }
    }