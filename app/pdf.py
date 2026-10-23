import fitz

def extract_pdf(path: str):
    doc = fitz.open(path)
    pages = []
    for page_number, page in enumerate(doc, start=1):
        pages.append({
            "page": page_number,
            "text": page.get_text("text").strip()
        })
    return {"pages": len(doc), "content": pages}
