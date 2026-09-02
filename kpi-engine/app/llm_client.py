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
    api_key = settings.openai_api_key or os.getenv('OPENAI_API_KEY', 'sk-mock-key')
    base_url = settings.openai_api_base or os.getenv('OPENAI_API_BASE', 'https://api.groq.com/openai/v1')
    model = settings.openai_model or os.getenv('OPENAI_MODEL', 'openai/gpt-oss-120b')

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
    from langchain_google_genai import ChatGoogleGenerativeAI
    api_key = os.getenv('GEMINI_API_KEY')
    return ChatGoogleGenerativeAI(
        model='gemini-2.5-flash',
        temperature=temperature,
        google_api_key=api_key
    )

def get_gemini_structured_llm(model_cls, temperature: float = 0.0):
    llm = get_gemini_chat_llm(temperature=temperature)
    return (
        llm.with_structured_output(model_cls)
    )

