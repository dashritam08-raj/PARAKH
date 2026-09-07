from pathlib import Path
import tempfile
import os

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

# Local Windows installation
WINDOWS_TESSERACT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Use the Windows executable when running locally.
# In cloud/Linux environments, pytesseract will use the
# Tesseract executable available in the system PATH.
if WINDOWS_TESSERACT_PATH.exists():
    pytesseract.pytesseract.tesseract_cmd = str(
        WINDOWS_TESSERACT_PATH
    )
else:
    cloud_tesseract = os.getenv("TESSERACT_CMD")

    if cloud_tesseract:
        pytesseract.pytesseract.tesseract_cmd = cloud_tesseract


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image):
    """
    Prepare product package image for OCR.
    """

    image = image.convert("RGB")

    width, height = image.size

    # Upscale image
    image = image.resize(
        (
            width * 2,
            height * 2
        ),
        Image.Resampling.LANCZOS
    )

    # Improve contrast
    image = ImageEnhance.Contrast(
        image
    ).enhance(1.5)

    # Improve sharpness
    image = ImageEnhance.Sharpness(
        image
    ).enhance(2.0)

    # Reduce small noise
    image = image.filter(
        ImageFilter.MedianFilter(size=3)
    )

    return image


# ============================================================
# TESSERACT
# ============================================================

def run_tesseract(image, config):

    return pytesseract.image_to_string(
        image,
        lang="eng+hin",
        config=config
    )


# ============================================================
# REMOVE DUPLICATE OCR LINES
# ============================================================

def clean_ocr_text(results):

    unique_lines = []

    for text in results:

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            # Ignore exact duplicate lines
            if line not in unique_lines:
                unique_lines.append(line)

    return "\n".join(unique_lines)


# ============================================================
# MAIN OCR FUNCTION
# ============================================================

def extract_text_from_image(image_bytes: bytes) -> str:

    if not image_bytes:
        raise ValueError(
            "Empty image received."
        )

    # Temporary image file
    with tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False
    ) as temp_file:

        temp_file.write(image_bytes)

        temp_path = Path(
            temp_file.name
        )

    try:

        # ----------------------------------------------------
        # Open image
        # ----------------------------------------------------

        image = Image.open(
            temp_path
        )

        # ----------------------------------------------------
        # Preprocess
        # ----------------------------------------------------

        processed = preprocess_image(
            image
        )

        # ----------------------------------------------------
        # OCR PASS 1
        # Product label / block text
        # ----------------------------------------------------

        text_1 = run_tesseract(
            processed,
            "--oem 3 --psm 6"
        )

        # ----------------------------------------------------
        # OCR PASS 2
        # Sparse text
        # ----------------------------------------------------

        text_2 = run_tesseract(
            processed,
            "--oem 3 --psm 11"
        )

        # ----------------------------------------------------
        # OCR PASS 3
        # Original image
        # ----------------------------------------------------

        text_3 = run_tesseract(
            image.convert("RGB"),
            "--oem 3 --psm 11"
        )

        # ----------------------------------------------------
        # Clean duplicates
        # ----------------------------------------------------

        combined = clean_ocr_text(
            [
                text_1,
                text_2,
                text_3
            ]
        )

        return combined.strip()

    finally:

        try:
            temp_path.unlink()

        except Exception:
            pass