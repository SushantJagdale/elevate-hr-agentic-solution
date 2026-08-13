"""Configuration module for Enterprise HR Agentic Virtual Assistant."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings:
    """Application settings loaded from environment or defaults."""
    
    # GCP / Model Configuration
    PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "learning-457908")
    LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)
    USE_VERTEXAI: bool = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
    
    # Retrieval Configuration
    RETRIEVAL_MODE: str = os.getenv("RETRIEVAL_MODE", "okf")  # okf, rag, hybrid
    KNOWLEDGE_DIR: Path = ROOT_DIR / "knowledge"
    DATA_DIR: Path = ROOT_DIR / "data"
    
    # Guardrails & Safety
    ENABLE_DLP_MASKING: bool = os.getenv("ENABLE_DLP_MASKING", "true").lower() == "true"
    GROUNDING_ATTRIBUTION_THRESHOLD: float = float(os.getenv("GROUNDING_ATTRIBUTION_THRESHOLD", "0.85"))
    DEDUPLICATION_WINDOW_HOURS: int = int(os.getenv("DEDUPLICATION_WINDOW_HOURS", "24"))
    
    # Audit Logging
    AUDIT_LOG_PATH: Path = ROOT_DIR / os.getenv("AUDIT_LOG_PATH", "logs/audit_vault.jsonl")
    
    # Server Configuration
    PORT: int = int(os.getenv("PORT", "8080"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

settings = Settings()
