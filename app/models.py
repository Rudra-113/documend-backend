from typing import Dict, List, Any
from pydantic import BaseModel, Field

class Document(BaseModel):
    id: str
    filename: str
    document_type: str = "unknown"
    pages: int = 0
    extracted_text: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)

class Case(BaseModel):
    id: str
    documents: List[Document] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    insurance: Dict[str, Any] = Field(default_factory=dict)
