from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    max_document_chars: int
    use_llm_fallback: bool

def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_document_chars=int(os.getenv("MAX_DOCUMENT_CHARS", "30000")),
        use_llm_fallback=os.getenv("ALLOW_DEMO_FALLBACK", "true").lower() == "true",
    )
