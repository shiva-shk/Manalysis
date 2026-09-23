"""Common result shape every connector normalizes into."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SearchResult:
    title: str
    entity_type: str
    source_name: str
    source_url: str
    source_type: str
    entity_name: Optional[str] = None
    company: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    regulatory_status: Optional[str] = None
    summary: Optional[str] = None
    identifier: Optional[str] = None
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    evidence_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "entity_type": self.entity_type,
            "entity_name": self.entity_name,
            "company": self.company,
            "country": self.country,
            "category": self.category,
            "regulatory_status": self.regulatory_status,
            "summary": self.summary,
            "identifier": self.identifier,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "retrieved_at": self.retrieved_at,
            "evidence_score": self.evidence_score,
        }


class ConnectorError(Exception):
    """Raised when a connector cannot complete a request (network, schema, etc.)."""
