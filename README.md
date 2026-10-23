# DocuMend Ledger — Backend

> **Understand your bill. Understand your insurance. Question anything that doesn't add up.**

DocuMend Ledger is an AI-powered medical billing and insurance document auditing system. The backend provides the APIs required to upload medical and insurance documents, extract structured information, analyze discrepancies, estimate insurance coverage, and answer questions using evidence from uploaded documents.

The backend is built with **FastAPI**, **PyMuPDF**, deterministic Python analysis, and the **Google Gemini API**.

---

## ✨ Features

- 📄 PDF document upload and text extraction
- 🤖 AI-powered document understanding
- 🧾 Hospital bill line-item extraction
- 🏥 Insurance policy extraction
- 🔍 Potential duplicate charge detection
- 🧮 Arithmetic/quantity discrepancy detection
- 📋 Cross-document analysis
- 💰 Insurance coverage estimation
- 💬 Ask DocuMend — document-grounded Q&A
- 📌 Evidence-linked responses
- 🔄 Re-analysis after adding additional documents
- 🌐 REST API for frontend integration
- ❤️ Health-check endpoint

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │   DocuMend Frontend │
                    │      Next.js        │
                    └──────────┬──────────┘
                               │ HTTPS
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI Backend  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌──────────────┐
       │ PDF Parser │   │ Gemini API │   │ Analysis     │
       │  PyMuPDF   │   │    AI      │   │ Engine       │
       └────────────┘   └────────────┘   └──────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │ Insurance Engine │
                     └──────────────────┘
```

---

## 📁 Project Structure

```text
documend-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── pdf.py
│   ├── gemma.py
│   ├── analysis.py
│   └── insurance.py
│
├── uploads/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── test_gemini.py
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend language |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| PyMuPDF | PDF text extraction |
| Google Gemini API | AI document understanding and Q&A |
| Pydantic | Request/data validation |
| python-dotenv | Environment configuration |

---

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Rudra-113/documend-backend.git
cd documend-backend
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
```

Never commit `.env` to GitHub.

### 5. Start the server

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 🔌 API Endpoints

### Health

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "service": "DocuMend Ledger"
}
```

### Create Case

```http
POST /api/cases
```

Creates a new audit case.

Example:

```json
{
  "case_id": "uuid"
}
```

### Upload Document

```http
POST /api/cases/{case_id}/documents
```

Accepts PDF documents.

Supported document categories include:

- Hospital bills
- Insurance policies
- Discharge summaries
- Prescriptions
- Diagnostic reports
- Receipts
- Claim letters
- Other supporting documents

### Analyze Case

```http
POST /api/cases/{case_id}/analyze
```

Runs the deterministic analysis and insurance analysis over all documents currently attached to the case.

### Get Case

```http
GET /api/cases/{case_id}
```

Returns documents, findings, insurance information, and analysis status.

### Get Findings

```http
GET /api/cases/{case_id}/findings
```

Returns detected findings.

### Get Insurance Analysis

```http
GET /api/cases/{case_id}/insurance
```

Returns the current insurance analysis.

### Ask DocuMend

```http
POST /api/cases/{case_id}/ask
```

Example request:

```json
{
  "question": "Why was this charge flagged?"
}
```

The response includes an answer, confidence, and supporting document/page evidence when available.

---

## 🧠 AI + Deterministic Analysis

DocuMend intentionally separates AI reasoning from deterministic calculations.

### AI handles

- Document classification
- Information extraction
- Understanding policy language
- Document-grounded question answering
- Evidence interpretation

### Python handles

- Arithmetic calculations
- Quantity × unit-price checks
- Duplicate detection
- Numeric processing
- Insurance-share calculations
- Deterministic rule checks

This reduces the risk of relying on an AI model for calculations that can be verified programmatically.

---

## 🔍 Analysis Workflow

```text
Upload documents
       ↓
Extract PDF text
       ↓
Classify document
       ↓
Extract structured information
       ↓
Store document in case
       ↓
Run deterministic analysis
       ↓
Run insurance analysis
       ↓
Generate findings
       ↓
Ask DocuMend / Evidence
```

Additional documents can be uploaded to an existing case and the same case can then be re-analyzed.

---

## 💰 Insurance Analysis

When both a hospital bill and insurance policy are available, DocuMend can estimate:

- Bill total
- Copay percentage
- Estimated insurance share
- Estimated patient share
- Policy exclusions

These are **estimates based on uploaded documents**.

Final insurance claim decisions remain with the insurer.

---

## ⚠️ Important Disclaimer

DocuMend is an auditing and document-understanding system.

It does not:

- Make final insurance claim decisions
- Determine legal liability
- Diagnose patients
- Prescribe medication
- Guarantee reimbursement
- Establish fraud solely from an anomaly

Findings should be treated as potential discrepancies or items requiring clarification and verification.

---

## 🌐 Production Deployment

The backend is deployed on **Render**.

Production API:

```text
https://documend-backend.onrender.com
```

API documentation:

```text
https://documend-backend.onrender.com/docs
```

Health check:

```text
https://documend-backend.onrender.com/health
```

### Render configuration

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Production environment variables:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
```

---

## 🔐 Security

Do not commit:

```text
.env
venv/
__pycache__/
uploads/
```

The Gemini API key must remain a server-side environment variable and must never be exposed to the frontend.

---

## 📄 License

This project was created as a hackathon/prototype project.

---

## 👨‍💻 Project

**DocuMend Ledger**

> Don't just read the bill. Audit it.
