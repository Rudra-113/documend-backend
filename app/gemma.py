import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to your .env file."
    )

client = genai.Client(api_key=API_KEY)


def ask_gemini(prompt: str):

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text


def clean_json(text: str):

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())


def extract_document(text: str):

    prompt = f"""
You are the document intelligence engine for DocuMend Ledger.

Analyze the uploaded document.

Determine the document type.

Possible document types:

- hospital_bill
- insurance_policy
- discharge_summary
- prescription
- diagnostic_report
- receipt
- claim_letter
- other

For hospital bills extract:

- document_type
- total
- dates
- items

Each item should contain:

- description
- quantity
- unit_price
- total
- page

For insurance policies extract:

- document_type
- rules
- copay_percent
- deductible
- exclusions

For medical documents extract:

- document_type
- diagnosis
- procedures
- tests
- dates
- important_facts

IMPORTANT:

1. Never invent information.
2. Use null when information is unavailable.
3. Preserve page numbers whenever possible.
4. Return ONLY valid JSON.
5. Do not return markdown.
6. Do not explain anything outside the JSON.

DOCUMENT:

{text[:60000]}
"""

    raw = ask_gemini(prompt)

    try:
        return clean_json(raw)

    except Exception:

        return {
            "document_type": "unknown",
            "parse_error": True,
            "raw_response": raw
        }


def answer_question(question: str, case_context: str):

    prompt = f"""
You are Ask DocuMend, an evidence-grounded
medical billing and insurance investigation assistant.

Answer the user's question using ONLY the supplied
case information.

Do not invent facts.

If the documents don't contain enough information,
say that clearly.

Every important conclusion should reference the
document and page supporting it.

Return ONLY valid JSON:

{{
    "answer": "clear answer",
    "confidence": 0.0,
    "evidence": [
        {{
            "document": "filename",
            "page": 1,
            "reason": "why this evidence supports the answer"
        }}
    ]
}}

QUESTION:

{question}

CASE INFORMATION:

{case_context}
"""

    raw = ask_gemini(prompt)

    try:
        return clean_json(raw)

    except Exception:

        return {
            "answer": raw,
            "confidence": 0.0,
            "evidence": []
        }