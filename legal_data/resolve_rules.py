from pathlib import Path
import json
import re


# ============================================================
# PARAKH — LEGAL RULE RESOLVER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

RULES_FILE = BASE_DIR / "rules" / "rules.json"
AMENDMENTS_FILE = BASE_DIR / "rules" / "amendments_rules.json"
OUTPUT_FILE = BASE_DIR / "rules" / "resolved_rules.json"


# ------------------------------------------------------------
# Load JSON
# ------------------------------------------------------------

def load_json(path):

    with path.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ------------------------------------------------------------
# Extract rule number
# ------------------------------------------------------------

def extract_rule_number(reference):

    match = re.search(
        r"Rule\s+(\d+)",
        reference,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return None


# ------------------------------------------------------------
# Build rule index
# ------------------------------------------------------------

def build_rule_index(rule_changes):

    index = {}

    for change in rule_changes:

        source = change.get(
            "source_document"
        )

        references = change.get(
            "rule_references",
            []
        )

        for reference in references:

            rule_number = extract_rule_number(
                reference
            )

            if rule_number is None:
                continue

            if rule_number not in index:

                index[rule_number] = []

            index[rule_number].append(
                {
                    "source_document": source,
                    "section_number":
                        change.get(
                            "section_number"
                        ),
                    "action":
                        change.get(
                            "action"
                        ),
                    "source_text":
                        change.get(
                            "source_text"
                        )
                }
            )

    return index


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print("=" * 70)
    print("PARAKH — LEGAL RULE RESOLVER")
    print("=" * 70)

    if not RULES_FILE.exists():

        print(
            f"\nERROR: Missing:\n{RULES_FILE}"
        )

        return

    if not AMENDMENTS_FILE.exists():

        print(
            f"\nERROR: Missing:\n{AMENDMENTS_FILE}"
        )

        return


    base_rules = load_json(
        RULES_FILE
    )

    amendment_data = load_json(
        AMENDMENTS_FILE
    )

    rule_changes = amendment_data.get(
        "rule_changes",
        []
    )


    rule_index = build_rule_index(
        rule_changes
    )


    # --------------------------------------------------------
    # Create resolved structure
    # --------------------------------------------------------

    resolved = {

        "schema_version": "1.0",

        "status":
            "research_stage",

        "warning":
            "This file indexes source-derived amendments. "
            "It is not a final legal interpretation.",

        "base_regulation":
            base_rules.get(
                "regulation",
                "Legal Metrology (Packaged Commodities) Rules, 2011"
            ),

        "rules": []
    }


    # --------------------------------------------------------
    # Add rules that appear in amendments
    # --------------------------------------------------------

    for rule_number in sorted(
        rule_index.keys()
    ):

        changes = rule_index[
            rule_number
        ]

        resolved["rules"].append(
            {
                "rule_number":
                    rule_number,

                "base_rule":
                    None,

                "amendments":
                    changes,

                "current_status":
                    "requires_legal_resolution"
            }
        )


    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.write_text(
        json.dumps(
            resolved,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


    print("\n" + "=" * 70)
    print("RESOLUTION INDEX CREATED")
    print("=" * 70)

    print(
        f"\nRules identified: "
        f"{len(resolved['rules'])}"
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()