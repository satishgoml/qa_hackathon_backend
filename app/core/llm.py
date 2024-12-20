from functools import cache
from typing import TypeAlias

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.schemas.llm_models import OpenAIModelName, GroqModelName, AllModelEnum

_MODEL_TABLE = {
    OpenAIModelName.GPT_4O_MINI: "gpt-4o-mini",
    OpenAIModelName.GPT_4O: "gpt-4o",
    GroqModelName.LLAMA_31_8B: "llama-3.1-8b-instant",
    GroqModelName.LLAMA_31_70B: "llama-3.1-70b-versatile",
    GroqModelName.LLAMA_GUARD_3_8B: "llama-guard-3-8b",
}

ModelT: TypeAlias = ChatOpenAI | ChatGroq


@cache
def get_model(model_name: AllModelEnum, /) -> ModelT:
    # NOTE: models with streaming=True will send tokens as they are generated
    # if the /stream endpoint is called with stream_tokens=True (the default)
    api_model_name = _MODEL_TABLE.get(model_name)

    if model_name in OpenAIModelName:
        return ChatOpenAI(model=api_model_name, temperature=0.5, streaming=True)
    if model_name in GroqModelName:
        if model_name == GroqModelName.LLAMA_GUARD_3_8B:
            return ChatGroq(model=api_model_name, temperature=0.0)
        return ChatGroq(model=api_model_name, temperature=0.5)
    raise ValueError(f"Unsupported model: {model_name}")
