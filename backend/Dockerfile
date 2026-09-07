FROM python:3.11-slim

# Install Tesseract OCR and required system libraries
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY app ./app
COPY check_db.py .

# Copy PARAKH legal rules
COPY legal_data ./legal_data

# Create runtime directories
RUN mkdir -p /app/data \
    /app/uploads \
    /app/generated_reports \
    /app/inspection_history

ENV PYTHONUNBUFFERED=1

# Start FastAPI
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]