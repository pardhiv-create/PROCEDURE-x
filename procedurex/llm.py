import json
from openai import OpenAI
from .config import get_settings

def get_client():
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=settings.openai_api_key)

def structured_response(model_class, instructions: str, payload: dict):
    settings = get_settings()
    client = get_client()
    response = client.responses.parse(
        model=settings.openai_model,
        input=[
            {"role":"system","content":instructions},
            {"role":"user","content":json.dumps(payload, ensure_ascii=False)}
        ],
        text_format=model_class,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("The model did not return a structured result.")
    return parsed
