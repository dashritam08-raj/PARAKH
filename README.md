PARAKH

AI-Assisted Legal Metrology Compliance Inspection

AI-Powered Compliance. Smarter Inspections. Safer Markets.

PARAKH is a web-based, AI-assisted inspection platform designed to help inspectors perform preliminary checks of packaged-product labels against machine-readable Legal Metrology requirements.

The system lets an inspector upload or capture a product image, extract label information with OCR, run structured compliance checks, review the findings, record a final human decision, and generate a digital inspection report.

Important: PARAKH is a decision-support system. It does not replace an authorized inspector or make an autonomous legal determination. OCR and automated rule checks can be incomplete or incorrect, so the final compliance decision remains with a human inspector.

✨ Key Features

📷 Image Upload & Camera Capture — inspect product packaging from uploaded images or a browser camera.

🔎 OCR-Based Extraction — extracts visible declarations such as MRP, net quantity, dates, and manufacturer information.

⚖️ Rule-Based Compliance Checks — evaluates extracted fields against structured compliance requirements.

👤 Human-in-the-Loop Verification — inspectors review findings, handle uncertainty, and make the final decision.

🗂️ Inspection History — stores inspection records for later review.

📄 Automated PDF Reports — generates standardized inspection documentation.

🔐 Authenticated Workflow — protected inspection operations with server-side sessions.

📱 Responsive Web Experience — designed for desktop and mobile browser workflows.

🧠 How PARAKH Works

Product Image
     │
     ▼
Image Processing
     │
     ▼
Tesseract OCR
     │
     ▼
Field Extraction & Normalization
     │
     ▼
Rule-Based Compliance Engine
     │
     ├───────────────┐
     ▼               ▼
 PASS / FAIL    NEEDS REVIEW
                     │
                     ▼
             Human Inspector
                     │
                     ▼
               Final Decision
                     │
                     ▼
              Inspection Record
                     │
                     ▼
                  PDF Report

🛠️ Technology Stack

Frontend

React

Vite

JavaScript / JSX

HTML5 / CSS3

React Router

Browser Camera API

Backend

Python

FastAPI

Uvicorn

REST APIs

AI / Intelligent Processing

Tesseract OCR via pytesseract

Pillow for image processing

Pattern-based field extraction

Machine-readable, rule-based compliance evaluation

Data & Reporting

SQLite

JSON-based compliance rules

ReportLab for PDF report generation

Security & Deployment

Argon2 password hashing

HttpOnly session cookies

Docker

📁 Project Structure

PARAKH/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── routes/
│   │   └── services/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── config/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── legal_data/
│   └── rules/
│       └── compliance_rules.json
│
├── data/
├── uploads/
└── README.md

🚀 Getting Started

Prerequisites

Make sure you have installed:

Python 3.10+

Node.js 18+

npm

Tesseract OCR

Git

1. Clone the repository

git clone https://github.com/dashritam08-raj/PARAKH.git
cd PARAKH

2. Set up the backend

cd backend
python -m venv .venv

Windows PowerShell

.venv\Scripts\Activate.ps1

macOS / Linux

source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Start the API:

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Backend API:

http://127.0.0.1:8000

Swagger documentation:

http://127.0.0.1:8000/docs

3. Set up the frontend

Open a second terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:5173

🔐 Environment Configuration

For local development, configure the frontend API endpoint using a Vite environment variable:

VITE_API_URL=http://localhost:8000

For a deployed environment, set VITE_API_URL to the public HTTPS URL of the FastAPI backend before rebuilding the frontend.

📸 Typical Inspection Workflow

Sign in as an inspector.

Open New Inspection.

Capture an image with the camera or upload a product image.

Start the analysis.

Review OCR-extracted declarations.

Review rule-based compliance findings.

Verify the evidence manually.

Record the final inspector decision.

Save the inspection.

Generate a PDF report.

🧩 Compliance Approach

PARAKH separates information extraction, automated checks, and human verification.

The compliance layer uses structured JSON rules so that individual requirements can be evaluated independently. A check can return statuses such as:

PASS

FAIL

NEEDS_REVIEW

NOT_CHECKED

This is intentional. An OCR error, incomplete image, missing declaration, or legal context that requires interpretation should not be silently converted into a definitive legal conclusion.

The current implementation is a prototype compliance rule set, not a complete legal interpretation engine. The repository also contains legal-reference data intended to support future expansion and amendment-aware rule maintenance.

🔒 Security Notes

The application includes:

Argon2 password hashing

Authenticated server-side sessions

HttpOnly cookies

Protected backend routes

Input and upload validation at the application layer

For production deployment, additional hardening is recommended, including stricter server-side upload controls, production database configuration, monitoring, secret management, and per-user authorization for inspection records.

🎯 Why PARAKH?

Government inspection workflows often involve repetitive visual checks, manual transcription, rule comparison, and documentation. PARAKH is designed to reduce that repetitive workload while preserving the inspector's role in the final decision.

Core principle

AI assists. Evidence informs. Humans decide.

🏆 Hackathon Context

PARAKH is built as a hackathon-ready prototype focused on GovTech, AI-assisted compliance, digital inspection, and public impact.

The project demonstrates an end-to-end workflow rather than a standalone AI prediction: capture → OCR → extraction → compliance checks → human verification → digital record → report.

📌 Project Links

GitHub: https://github.com/dashritam08-raj/PARAKH

Live Demo: https://parakh-fawn.vercel.app

The live demo requires a correctly configured production FastAPI backend/API URL. For local development, follow the setup instructions above.

👥 Team

Built for hackathon and innovation use by the PARAKH team.

