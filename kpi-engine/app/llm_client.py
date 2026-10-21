import os
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from app.config import settings

def make_strict_schema(model_cls):
    schema = model_cls.model_json_schema()

    def _enforce_additional_properties(node):
        if isinstance(node, dict):
            if node.get('type') == 'object' and 'additionalProperties' not in node:
                node['additionalProperties'] = False
            for v in node.values():
                _enforce_additional_properties(v)
        elif isinstance(node, list):
            for item in node:
                _enforce_additional_properties(item)

    _enforce_additional_properties(schema)
    return schema

def get_chat_llm(temperature: float = 0.0):
    api_key = (
        settings.groq_api_key
        or settings.openai_api_key
        or os.getenv('GROQ_API_KEY')
        or os.getenv('OPENAI_API_KEY')
    )
    base_url = settings.openai_api_base or os.getenv('OPENAI_API_BASE', 'https://api.groq.com/openai/v1')
    model = settings.openai_model or os.getenv('OPENAI_MODEL', 'openai/gpt-oss-20b')

    return ChatOpenAI(
        model=model,
        base_url=base_url,
        temperature=temperature,
        api_key=api_key
    )

def get_structured_llm(model_cls, temperature: float = 0.0):
    llm = get_chat_llm(temperature=temperature)
    strict_schema = make_strict_schema(model_cls)

    return (
        llm.with_structured_output(strict_schema)
        | RunnableLambda(lambda d: model_cls.model_validate(d) if isinstance(d, dict) else d)
    )

def get_gemini_chat_llm(temperature: float = 0.0):
    return get_chat_llm(temperature=temperature)

def get_gemini_structured_llm(model_cls, temperature: float = 0.0):
    return get_structured_llm(model_cls, temperature=temperature)
