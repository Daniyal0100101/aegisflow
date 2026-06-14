import os
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Load .env file from project root if present
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

class Settings(BaseModel):
    """FastAPI application settings validated using Pydantic."""
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    port: int = int(os.getenv("PORT", "8000"))
    env_name: str = os.getenv("ENV_NAME", "development")
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

settings = Settings()
