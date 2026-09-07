from pathlib import Path

import pytesseract
from pdf2image import convert_from_path


# ============================================================
# PARAKH OCR CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SOURCE_DIR = BASE_DIR / "source_documents"
OUTPUT_DIR = BASE_DIR / "extracted_text"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Tesseract installation
TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# Poppler installation
POPPLER_PATH = (
    r"C:\poppler\poppler-26.02.0\Library\bin"
)


# OCR language
OCR_LANGUAGE = "eng+hin"


# ============================================================
# OCR ONE PDF
# ============================================================

def extract_pdf_with_ocr(pdf_path: Path) -> str:

    print(f"\nProcessing: {pdf_path.name}")

    print("Converting PDF pages to images...")

    pages = convert_from_path(
        pdf_path,
        dpi=250,
        poppler_path=POPPLER_PATH
    )

    print(f"Total pages: {len(pages)}")

    extracted_pages = []

    for page_number, page_image in enumerate(
        pages,
        start=1
    ):

        print(
            f"  OCR page {page_number}/{len(pages)}..."
        )

        text = pytesseract.image_to_string(
            page_image,
            lang=OCR_LANGUAGE
        )

        extracted_pages.append(
            f"\n\n===== PAGE {page_number} =====\n\n"
            f"{text}"
        )

    return "".join(extracted_pages)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PARAKH LEGAL DOCUMENT OCR")
    print("=" * 60)

    if not SOURCE_DIR.exists():

        print(
            f"\nERROR: Source folder not found:\n"
            f"{SOURCE_DIR}"
        )

        return
    pdf_files = [
    SOURCE_DIR / "2011.pdf"
    ]

    if not pdf_files:

        print(
            "\nERROR: No PDF files found."
        )

        return

    print(
        f"\nFound {len(pdf_files)} PDF files."
    )

    successful = 0
    failed = 0

    for pdf_path in pdf_files:

        try:

            text = extract_pdf_with_ocr(
                pdf_path
            )

            output_file = (
                OUTPUT_DIR /
                f"{pdf_path.stem}.txt"
            )

            output_file.write_text(
                text,
                encoding="utf-8"
            )

            print(
                f"Saved: {output_file}"
            )

            successful += 1

        except Exception as error:

            print(
                f"\nERROR processing "
                f"{pdf_path.name}:"
            )

            print(error)

            failed += 1

    print("\n" + "=" * 60)
    print("OCR COMPLETE")
    print("=" * 60)

    print(
        f"Successful: {successful}"
    )

    print(
        f"Failed:     {failed}"
    )

    print(
        f"\nOutput folder:\n"
        f"{OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()