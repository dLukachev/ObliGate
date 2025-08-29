from typing import Optional, List
from pydantic import BaseModel

class Citation(BaseModel):
    text: str
    page: Optional[int] = None      # для PDF
    bbox: Optional[List[float]] = None
    paragraph_index: Optional[int] = None  # для DOCX
    run_index: Optional[int] = None
    
class Requisites(BaseModel):
    inn: Optional[Citation]
    kpp: Optional[Citation]
    ogrn: Optional[Citation]

class DocsInfo(BaseModel):
    party_1_name: Optional[Citation]
    party_2_name: Optional[Citation]
    contract_date: Optional[Citation]
    contract_start: Optional[Citation]
    contract_end: Optional[Citation]
    subject: Optional[Citation]
    delivery_terms: Optional[Citation]
    payment_terms: Optional[Citation]
    amount: Optional[Citation]
    currency: Optional[Citation]
    penalty_present: Optional[Citation]
    penalty_amount_or_formula: Optional[Citation]
    extension_possible: Optional[Citation]
    extension_conditions: Optional[Citation]
    termination_conditions: Optional[Citation]
    requisites: Optional[Requisites]
