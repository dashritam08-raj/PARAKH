from pathlib import Path
import re


# ============================================================
# PARAKH — AUTOMATIC AMENDMENT SCANNER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

TEXT_DIR = BASE_DIR / "extracted_text"
OUTPUT_FILE = BASE_DIR / "metadata" / "amendment_scan.txt"


def find_rule_references(text):
    """
    Find references such as:
    rule 6
    rule 7
    rule 6(1)
    rule 6, in sub-rule (11)
    """

    patterns = [
        r"\brule\s+(\d+)",
        r"\brule\s+(\d+)\s*,?\s*in\s+sub-rule\s*\((\d+)\)",
        r"\brule\s+(\d+)\s*,?\s*in\s+clause\s*\(([^)]+)\)",
    ]

    matches = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE
        ):
            matches.append(match.group(0))

    return sorted(
        set(matches),
        key=str.lower
    )


def find_amendment_keywords(text):
    """
    Find words that commonly indicate
    modifications to existing rules.
    """

    keywords = [
        "shall be substituted",
        "shall be inserted",
        "shall be omitted",
        "shall be replaced",
        "shall be amended",
        "in rule",
        "in sub-rule",
        "in clause",
        "after sub-rule",
        "before sub-rule",
        "following shall be inserted",
        "following shall be substituted"
    ]

    found = []

    lower_text = text.lower()

    for keyword in keywords:

        if keyword.lower() in lower_text:
            found.append(keyword)

    return found


def get_context(text, keyword, window=500):

    position = text.lower().find(
        keyword.lower()
    )

    if position == -1:
        return ""

    start = max(
        0,
        position - window
    )

    end = min(
        len(text),
        position + len(keyword) + window
    )

    return text[start:end].replace(
        "\n",
        " "
    )


def scan_document(file_path):

    text = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    rules = find_rule_references(text)

    keywords = find_amendment_keywords(text)

    return {
        "file": file_path.name,
        "rules": rules,
        "keywords": keywords,
        "is_amendment": bool(
            rules and keywords
        )
    }


def main():

    print("=" * 65)
    print("PARAKH — AUTOMATIC AMENDMENT SCANNER")
    print("=" * 65)

    if not TEXT_DIR.exists():

        print(
            f"\nERROR: Folder not found:\n"
            f"{TEXT_DIR}"
        )

        return

    text_files = sorted(
        TEXT_DIR.glob("*.txt")
    )

    if not text_files:

        print("\nERROR: No OCR text files found.")

        return

    print(
        f"\nFound {len(text_files)} OCR files.\n"
    )

    reports = []

    for file_path in text_files:

        result = scan_document(
            file_path
        )

        reports.append(result)

        print("-" * 65)
        print(
            f"FILE: {result['file']}"
        )

        if result["is_amendment"]:

            print("STATUS: Possible amendment")

            print("\nRule references:")

            for rule in result["rules"]:
                print(f"  • {rule}")

            print("\nAmendment keywords:")

            for keyword in result["keywords"]:
                print(f"  • {keyword}")

        else:

            print(
                "STATUS: No obvious amendment pattern"
            )

    # --------------------------------------------------------
    # Save report
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as output:

        output.write(
            "PARAKH AUTOMATIC AMENDMENT SCAN\n"
        )

        output.write(
            "=" * 65 + "\n\n"
        )

        for result in reports:

            output.write(
                f"FILE: {result['file']}\n"
            )

            output.write(
                f"STATUS: "
                f"{'Possible amendment' if result['is_amendment'] else 'No obvious amendment pattern'}\n"
            )

            output.write(
                "\nRULE REFERENCES:\n"
            )

            for rule in result["rules"]:

                output.write(
                    f"  - {rule}\n"
                )

            output.write(
                "\nAMENDMENT KEYWORDS:\n"
            )

            for keyword in result["keywords"]:

                output.write(
                    f"  - {keyword}\n"
                )

            output.write(
                "\n" + "-" * 65 + "\n\n"
            )

    print("\n" + "=" * 65)
    print("SCAN COMPLETE")
    print("=" * 65)

    print(
        f"\nReport saved to:\n"
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()