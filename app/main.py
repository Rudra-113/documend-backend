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


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="DocuMend Ledger API",
    description="AI-powered medical billing and insurance document auditor",
    version="0.2.0",
)


# ============================================================
# CORS
# Allows the Next.js frontend to communicate with FastAPI
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STORAGE
# ============================================================

CASES = {}

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# REQUEST MODELS
# ============================================================

class AskRequest(BaseModel):
    question: str


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "DocuMend Ledger"
    }


# ============================================================
# CREATE CASE
# ============================================================

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


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.post("/api/cases/{case_id}/documents")
async def upload_document(
    case_id: str,
    file: UploadFile = File(...)
):

    # Check case
    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    # Check file name
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )

    # Currently supporting PDF
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # Generate document ID
    document_id = str(uuid.uuid4())

    # Protect filename
    safe_filename = os.path.basename(file.filename)

    stored_filename = f"{document_id}_{safe_filename}"

    path = os.path.join(
        UPLOAD_DIR,
        stored_filename
    )

    # Read uploaded file
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    # Save file
    with open(path, "wb") as f:
        f.write(content)

    # --------------------------------------------------------
    # PDF EXTRACTION
    # --------------------------------------------------------

    try:
        pdf_data = extract_pdf(path)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read PDF: {exc}"
        )

    # Combine page text for AI extraction
    full_text = "\n".join(
        page["text"]
        for page in pdf_data["content"]
        if page.get("text")
    )

    # --------------------------------------------------------
    # AI DOCUMENT EXTRACTION
    # --------------------------------------------------------

    try:

        extracted_data = extract_document(
            full_text
        )

    except Exception as exc:

        extracted_data = {
            "document_type": "unknown",
            "ai_error": str(exc)
        }

    # --------------------------------------------------------
    # DOCUMENT OBJECT
    # --------------------------------------------------------

    document = {
        "id": document_id,
        "filename": safe_filename,
        "pages": pdf_data["pages"],
        "extracted_text": pdf_data["content"],
        "extracted_data": extracted_data,
    }

    # Add document to case
    CASES[case_id]["documents"].append(
        document
    )

    # New document means previous analysis may be outdated
    CASES[case_id]["analysis_status"] = "needs_reanalysis"

    return {
        "message": "Document uploaded",
        "document": document
    }


# ============================================================
# ANALYZE CASE
# ============================================================

@app.post("/api/cases/{case_id}/analyze")
def analyze(case_id: str):

    # Check case
    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    case = CASES[case_id]

    # Need documents
    if not case["documents"]:
        raise HTTPException(
            status_code=400,
            detail="No documents uploaded for this case"
        )

    # Mark as analyzing
    case["analysis_status"] = "analyzing"

    try:

        # ----------------------------------------------------
        # DETERMINISTIC ANALYSIS
        # ----------------------------------------------------

        findings = analyze_case(
            case["documents"]
        )

        # ----------------------------------------------------
        # INSURANCE ANALYSIS
        # ----------------------------------------------------

        insurance = analyze_insurance(
            case["documents"]
        )

        # Save results
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


# ============================================================
# GET COMPLETE CASE
# ============================================================

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


# ============================================================
# GET FINDINGS
# ============================================================

@app.get("/api/cases/{case_id}/findings")
def get_findings(case_id: str):

    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return {
        "case_id": case_id,
        "findings": CASES[case_id]["findings"],
    }


# ============================================================
# GET INSURANCE ANALYSIS
# ============================================================

@app.get("/api/cases/{case_id}/insurance")
def get_insurance(case_id: str):

    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return {
        "case_id": case_id,
        "insurance": CASES[case_id]["insurance"],
    }


# ============================================================
# ASK DOCUMEND
# ============================================================

@app.post("/api/cases/{case_id}/ask")
def ask_documend(
    case_id: str,
    request: AskRequest
):

    # Check case
    if case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    # Validate question
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    case = CASES[case_id]

    # Need documents
    if not case["documents"]:
        raise HTTPException(
            status_code=400,
            detail="No documents available for this case"
        )

    # --------------------------------------------------------
    # BUILD AI CONTEXT
    # --------------------------------------------------------

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

    # Convert to JSON
    context_json = json.dumps(
        context,
        ensure_ascii=False
    )

    # Keep context within reasonable model size
    context_json = context_json[:90000]

    # --------------------------------------------------------
    # ASK GEMINI
    # --------------------------------------------------------

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