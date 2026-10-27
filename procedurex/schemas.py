from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

class Requirements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    natural_language: str = Field(description="Original purchase requirement in natural language")
    quantity: int = Field(gt=0)
    min_ram_gb: int = Field(ge=0)
    min_ssd_gb: int = Field(ge=0)
    min_warranty_years: int = Field(ge=0)
    max_unit_price: float = Field(gt=0)
    max_delivery_days: Optional[int] = Field(default=None, ge=0)
    preferences: str = ""

class EvidenceItem(BaseModel):
    field: str
    quote: str = Field(description="Short verbatim quote supporting the extracted field; empty if unknown")
    location: str = Field(description="Page, sheet, section or approximate location if known; otherwise unknown")

class QuotationExtraction(BaseModel):
    vendor_name: Optional[str] = None
    product_name: Optional[str] = None
    model_number: Optional[str] = None
    unit_price: Optional[float] = Field(default=None, description="Numeric unit price, excluding tax if stated that way")
    currency: str = "INR"
    quantity: Optional[int] = None
    ram_gb: Optional[float] = None
    ssd_gb: Optional[float] = None
    processor: Optional[str] = None
    processor_tier: Optional[int] = Field(default=None, description="Approximate tier: 3, 5, 7, 9; null if unclear")
    warranty_years: Optional[float] = None
    warranty_type: Optional[str] = None
    delivery_days: Optional[int] = None
    tax_percent: Optional[float] = None
    other_fees: Optional[float] = None
    payment_terms: Optional[str] = None
    confidence: float = Field(ge=0, le=1)
    missing_fields: list[str]
    evidence: list[EvidenceItem]
    extraction_method: Literal["llm", "fallback"] = "llm"

class Tradeoff(BaseModel):
    vendor: str
    analysis: str

class RecommendationSynthesis(BaseModel):
    recommended_vendor: Optional[str]
    recommendation_summary: str
    tradeoffs: list[Tradeoff]
    clarification_questions: list[str]
    risks: list[str]
    llm_used: bool = True
