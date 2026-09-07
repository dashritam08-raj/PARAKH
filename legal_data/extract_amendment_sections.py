from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parent

TEXT_DIR = BASE_DIR / "extracted_text"
OUTPUT_DIR = BASE_DIR / "metadata"
OUTPUT_FILE = OUTPUT_DIR / "amendment_sections.txt"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


AMENDMENT_PATTERNS = [
    r"in the said rules.*?(?=\n\s*\d+\.)",
    r"in rule\s+\d+.*?(?=\n\s*\d+\.)",
    r"shall be substituted.*?(?=\n\s*\d+\.)",
    r"shall be inserted.*?(?=\n\s*\d+\.)",
    r"shall be omitted.*?(?=\n\s*\d+\.)",
    r"shall be replaced.*?(?=\n\s*\d+\.)",
]


def clean_text(text):

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def extract_sections(text):

    sections = []

    # Look for numbered amendment paragraphs.
    numbered = re.split(
        r"\n(?=\s*\d+\.\s)",
        text
    )

    for section in numbered:

        lower = section.lower()

        if any(
            keyword in lower
            for keyword in [
                "shall be substituted",
                "shall be inserted",
                "shall be omitted",
                "shall be replaced",
                "in rule",
                "in sub-rule",
                "in clause"
            ]
        ):

            section = clean_text(section)

            if len(section) > 40:
                sections.append(section)

    return sections


def main():

    print("=" * 70)
    print("PARAKH — AMENDMENT SECTION EXTRACTOR")
    print("=" * 70)

    files = sorted(
        TEXT_DIR.glob("*.txt")
    )

    print(
        f"\nScanning {len(files)} OCR files..."
    )

    total_sections = 0

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as output:

        for file_path in files:

            text = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            sections = extract_sections(text)

            if not sections:
                continue

            print(
                f"\n{file_path.name}: "
                f"{len(sections)} section(s)"
            )

            output.write(
                "\n" + "=" * 70 + "\n"
            )

            output.write(
                f"SOURCE: {file_path.name}\n"
            )

            output.write(
                "=" * 70 + "\n\n"
            )

            for number, section in enumerate(
                sections,
                start=1
            ):

                output.write(
                    f"[AMENDMENT SECTION {number}]\n\n"
                )

                output.write(
                    section
                )

                output.write(
                    "\n\n"
                )

                total_sections += 1

    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)

    print(
        f"\nAmendment sections found: "
        f"{total_sections}"
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()