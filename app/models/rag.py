"""RAG and Policy Knowledge Data Models matching SDD Section 3.5.2."""

from datetime import datetime
from pydantic import BaseModel, Field


class RAGChunkMetadataSchema(BaseModel):
    document_id: str
    document_name: str
    section_title: str
    section_id: str
    gcs_source_uri: str
    deep_link_url: str
    chunk_id: str
    chunk_text: str
    embedding_vector: list[float] | None = None
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    access_control_roles: list[str] = Field(default_factory=lambda: ["all_employees"])


class PolicyDocument(BaseModel):
    doc_id: str
    title: str
    category: str
    content: str
    file_path: str
    sections: list[RAGChunkMetadataSchema] = Field(default_factory=list)


class GroundingResult(BaseModel):
    query: str
    chunks: list[RAGChunkMetadataSchema]
    attribution_score: float = 0.0
    is_grounded: bool = False
    source_citations: list[str] = Field(default_factory=list)
