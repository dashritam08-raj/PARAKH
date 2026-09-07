from pathlib import Path
from pypdf import PdfReader


# PARAKH legal-data folders
BASE_DIR = Path(__file__).resolve().parent

SOURCE_DIR = BASE_DIR / "source_documents"
OUTPUT_DIR = BASE_DIR / "extracted_text"

# Create output folder if it doesn't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text from every page of a PDF.
    """

    print(f"\nReading: {pdf_path.name}")

    reader = PdfReader(str(pdf_path))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        try:
            text = page.extract_text() or ""

            pages.append(
                f"\n\n===== PAGE {page_number} =====\n\n"
                f"{text}"
            )

        except Exception as error:
            print(
                f"  Warning: Could not read page "
                f"{page_number}: {error}"
            )

    return "".join(pages)


def main():

    pdf_files = sorted(SOURCE_DIR.glob("*.pdf"))

    if not pdf_files:
        print("ERROR: No PDF files found.")
        print(f"Check this folder:")
        print(SOURCE_DIR)
        return

    print("=" * 60)
    print("PARAKH LEGAL DOCUMENT EXTRACTOR")
    print("=" * 60)

    print(f"\nFound {len(pdf_files)} PDF files.")

    successful = 0
    failed = 0

    for pdf_path in pdf_files:

        try:

            text = extract_pdf_text(pdf_path)

            # Same filename, but .txt
            output_file = OUTPUT_DIR / f"{pdf_path.stem}.txt"

            output_file.write_text(
                text,
                encoding="utf-8"
            )

            print(
                f"Saved: {output_file.name}"
            )

            successful += 1

        except Exception as error:

            print(
                f"ERROR processing {pdf_path.name}: "
                f"{error}"
            )

            failed += 1

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)

    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print(f"\nOutput folder:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()