"""Company model and response schema (maps to `company` table)."""

from pydantic import BaseModel


class CompanyResponse(BaseModel):
    id_company: int
    name: str
    sector: str | None = None
    email: str | None = None
    country: str | None = None
    score: int | None = None
    tech: str | None = None

    class Config:
        from_attributes = True
