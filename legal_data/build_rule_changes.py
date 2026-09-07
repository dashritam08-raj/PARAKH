from pathlib import Path
import json
import re


# ============================================================
# PARAKH — BUILD STRUCTURED RULE CHANGES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "metadata" / "amendment_sections.txt"
OUTPUT_FILE = BASE_DIR / "rules" / "amendments_rules.json"


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def detect_action(text):
    text_lower = text.lower()

    if "shall be substituted" in text_lower:
        return "substitute"

    if "shall be inserted" in text_lower:
        return "insert"

    if "shall be omitted" in text_lower:
        return "omit"

    if "shall be replaced" in text_lower:
        return "replace"

    return "other"


def extract_rule_references(text):
    """
    Find references such as:

    rule 6
    rule 6, in sub-rule (11)
    rule 26
    rule 26 in clause (a)
    """

    references = []

    patterns = [
        r"\brule\s+(\d+)\s*,?\s*in\s+sub-rule\s*\(([^)]+)\)",
        r"\brule\s+(\d+)\s+in\s+sub-rule\s*\(([^)]+)\)",
        r"\brule\s+(\d+)\s*,?\s*in\s+clause\s*\(([^)]+)\)",
        r"\brule\s+(\d+)",
    ]

    for pattern in patterns:

        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE
        ):

            groups = match.groups()

            if len(groups) == 2:

                rule_number = groups[0]
                detail = groups[1]

                references.append(
                    f"Rule {rule_number} ({detail})"
                )

            else:

                references.append(
                    f"Rule {groups[0]}"
                )

    # Remove duplicates
    return list(dict.fromkeys(references))


def extract_source_sections(text):
    """
    Split amendment report into individual source sections.
    """

    pattern = r"={20,}\s*SOURCE:\s*(.*?)\s*={20,}"

    matches = list(
        re.finditer(
            pattern,
            text,
            re.IGNORECASE
        )
    )

    sections = []

    for index, match in enumerate(matches):

        source = match.group(1).strip()

        start = match.end()

        if index + 1 < len(matches):

            end = matches[index + 1].start()

        else:

            end = len(text)

        content = text[start:end].strip()

        sections.append(
            {
                "source": source,
                "content": content
            }
        )

    return sections


def extract_amendment_blocks(content):
    """
    Extract [AMENDMENT SECTION X] blocks.
    """

    pattern = (
        r"\[AMENDMENT SECTION\s+(\d+)\]"
        r"(.*?)(?=\[AMENDMENT SECTION|\Z)"
    )

    matches = re.findall(
        pattern,
        content,
        re.IGNORECASE | re.DOTALL
    )

    blocks = []

    for number, block in matches:

        block = block.strip()

        if block:

            blocks.append(
                {
                    "section_number": int(number),
                    "text": block
                }
            )

    return blocks


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print("=" * 70)
    print("PARAKH — BUILD STRUCTURED RULE CHANGES")
    print("=" * 70)

    if not INPUT_FILE.exists():

        print(
            f"\nERROR: Input file not found:\n"
            f"{INPUT_FILE}"
        )

        return

    text = INPUT_FILE.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    source_sections = extract_source_sections(
        text
    )

    rule_changes = []

    for source_section in source_sections:

        source = source_section["source"]
        content = source_section["content"]

        blocks = extract_amendment_blocks(
            content
        )

        for block in blocks:

            amendment_text = block["text"]

            references = extract_rule_references(
                amendment_text
            )

            action = detect_action(
                amendment_text
            )

            rule_changes.append(
                {
                    "source_document": source.replace(
                        ".txt",
                        ".pdf"
                    ),
                    "section_number":
                        block["section_number"],
                    "rule_references":
                        references,
                    "action":
                        action,
                    "source_text":
                        amendment_text
                }
            )

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output = {
        "schema_version": "1.0",
        "description":
            "Machine-readable index of amendment sections extracted from official OCR text.",
        "warning":
            "This file preserves source text and detected patterns. It is not a final legal interpretation.",
        "rule_changes":
            rule_changes
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)

    print(
        f"\nStructured sections: "
        f"{len(rule_changes)}"
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()