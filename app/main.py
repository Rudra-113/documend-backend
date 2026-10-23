import json
import os
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.pdf import extract_pdf
from app.gemma import extract_document, answer_question
from app.analysis import analyze_case
from app.insurance import analyze_insurance


app = FastAPI(
    title="DocuMend Ledger API",
    description="AI-powered medical billing and insurance document auditor",
    version="0.2.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
# Allows the deployed frontend (Vercel) and local frontend
# to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Storage
# ---------------------------------------------------------

CASES = {}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class AskRequest(BaseModel):
    question: str


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "DocuMend Ledger"
    }


# ---------------------------------------------------------
# Create Case
# ---------------------------------------------------------

@app.post("/api/cases")
def create_case():
    case_id = str(uuid.uuid4())

    CASES[case_id] = {
        "id": case_id,
        "documents": [],
        "findings": [],
        "insurance": {},
        "analysis_status": "not_analyzed",
    }

    return {
        "case_id": case_id
    }


# ---------------------------------------------------------
# Upload Document
# ---------------------------------------------------------

@app.post("/api/cases/{case_id}/documents")
async def upload_document(
    case_id: str,
    file: UploadFile = File(...)
):
    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    document_id = str(uuid.uuid4())

    safe_filename = os.path.basename(file.filename)

    stored_filename = f"{document_id}_{safe_filename}"

    path = os.path.join(
        UPLOAD_DIR,
        stored_filename
    )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    with open(path, "wb") as f:
        f.write(content)

    # ---------------------------------------------
    # Extract PDF text
    # ---------------------------------------------

    try:
        pdf_data = extract_pdf(path)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read PDF: {exc}"
        )

    full_text = "\n".join(
        page["text"]
        for page in pdf_data["content"]
        if page.get("text")
    )

    # ---------------------------------------------
    # AI document extraction
    # ---------------------------------------------

    try:
        extracted_data = extract_document(full_text)

    except Exception as exc:
        extracted_data = {
            "document_type": "unknown",
            "ai_error": str(exc)
        }

    # ---------------------------------------------
    # Store document
    # ---------------------------------------------

    document = {
        "id": document_id,
        "filename": safe_filename,
        "pages": pdf_data["pages"],
        "extracted_text": pdf_data["content"],
        "extracted_data": extracted_data,
    }

    CASES[case_id]["documents"].append(document)

    # Adding a document means the previous analysis
    # is no longer guaranteed to represent the full case.
    CASES[case_id]["analysis_status"] = "needs_reanalysis"

    return {
        "message": "Document uploaded",
        "document": document
    }


# ---------------------------------------------------------
# Analyze Case
# ---------------------------------------------------------

@app.post("/api/cases/{case_id}/analyze")
def analyze(case_id: str):

    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    case = CASES[case_id]

    if not case["documents"]:
        raise HTTPException(
            status_code=400,
            detail="No documents uploaded for this case"
        )

    case["analysis_status"] = "analyzing"

    try:

        # Deterministic analysis
        findings = analyze_case(
            case["documents"]
        )

        # Insurance analysis
        insurance = analyze_insurance(
            case["documents"]
        )

        case["findings"] = findings

        case["insurance"] = insurance

        case["analysis_status"] = "complete"

    except Exception as exc:

        case["analysis_status"] = "failed"

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}"
        )

    return {
        "case_id": case_id,
        "document_count": len(case["documents"]),
        "analysis_status": case["analysis_status"],
        "findings": case["findings"],
        "insurance": case["insurance"],
    }


# ---------------------------------------------------------
# Get Complete Case
# ---------------------------------------------------------

@app.get("/api/cases/{case_id}")
def get_case(case_id: str):

    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    case = CASES[case_id]

    return {
        "id": case["id"],
        "document_count": len(case["documents"]),
        "documents": case["documents"],
        "findings": case["findings"],
        "insurance": case["insurance"],
        "analysis_status": case["analysis_status"],
    }


# ---------------------------------------------------------
# Get Findings
# ---------------------------------------------------------

@app.get("/api/cases/{case_id}/findings")
def get_findings(case_id: str):

    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return {
        "case_id": case_id,
        "findings": CASES[case_id]["findings"]
    }


# ---------------------------------------------------------
# Get Insurance Analysis
# ---------------------------------------------------------

@app.get("/api/cases/{case_id}/insurance")
def get_insurance(case_id: str):

    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return {
        "case_id": case_id,
        "insurance": CASES[case_id]["insurance"]
    }


# ---------------------------------------------------------
# Ask DocuMend
# ---------------------------------------------------------

@app.post("/api/cases/{case_id}/ask")
def ask_documend(
    case_id: str,
    request: AskRequest
):

    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    case = CASES[case_id]

    if not case["documents"]:
        raise HTTPException(
            status_code=400,
            detail="No documents available for this case"
        )

    # ---------------------------------------------
    # Build evidence-grounded context
    # ---------------------------------------------

    context = {
        "documents": [
            {
                "filename": document["filename"],
                "pages": document["pages"],
                "extracted_data": document["extracted_data"],
                "page_text": document["extracted_text"],
            }
            for document in case["documents"]
        ],

        "findings": case["findings"],

        "insurance": case["insurance"],
    }

    # Prevent excessively large AI requests.
    context_json = json.dumps(
        context,
        ensure_ascii=False
    )[:90000]

    # ---------------------------------------------
    # Ask Gemini
    # ---------------------------------------------

    try:

        result = answer_question(
            question,
            context_json
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {exc}"
        )

    return result