# DocuMend Ledger Backend

FastAPI backend for the DocuMend Ledger hackathon prototype.

## Setup

PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill in `.env` with the Gemma provider endpoint and API key.

## Run

```powershell
uvicorn app.main:app --reload
```

Open:

http://127.0.0.1:8000/docs

## Flow

1. POST `/api/cases`
2. POST `/api/cases/{case_id}/documents` with a PDF
3. POST `/api/cases/{case_id}/analyze`
4. GET `/api/cases/{case_id}`
5. POST `/api/cases/{case_id}/ask`

The prototype keeps case data in memory, so restarting the server clears cases.
