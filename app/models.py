from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MarketSource(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    published_at: str | None = None


class AnalyzeContext(BaseModel):
    sector: str
    user_type: Literal["guest", "api_key"]
    session_id: str
    requested_at: datetime
    sources: list[MarketSource] = Field(default_factory=list)


class SearchResult(BaseModel):
    sector: str
    query: str
    sources: list[MarketSource] = Field(default_factory=list)


class AnalyzeRequestPath(BaseModel):
    sector: str = Field(min_length=2, max_length=40)

    @field_validator("sector")
    @classmethod
    def validate_sector(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized.replace("-", " ").replace("&", "").replace("/", "").replace(" ", "").isalnum():
            raise ValueError("Sector must only contain letters, numbers, spaces, hyphens, slash, or ampersand")
        return " ".join(normalized.split())
