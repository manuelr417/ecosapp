import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from openai import AsyncOpenAI

from .config import Settings
from .schemas import Detection

NARRATION_SYSTEM_PROMPT = (
    "You are a friendly science presenter talking to high school students. "
    "Describe in 2 or 3 very short sentences what was found in the image. "
    "Use simple, fun language. Never mention percentages or technical terms."
)


@dataclass(frozen=True)
class LLMProvider:
    base_url: str
    model: str
    api_key: str = "local"


def build_providers(settings: Settings) -> list[LLMProvider]:
    return [
        LLMProvider(settings.llm_primary_base_url, settings.llm_primary_model),
        LLMProvider(
            settings.llm_fallback_base_url,
            settings.llm_fallback_model,
            settings.llm_fallback_api_key,
        ),
    ]


def build_messages(detections: list[Detection]) -> list[dict]:
    if detections:
        summary = ", ".join(
            f"{d.label} ({round(d.confidence * 100)}% sure)" for d in detections
        )
        user_text = f"Objects detected in the image: {summary}. Tell the audience what you see."
    else:
        user_text = (
            "No familiar objects were recognized in the image. "
            "Tell the audience that in a fun way."
        )
    return [
        {"role": "system", "content": NARRATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]


async def stream_from_provider(
    provider: LLMProvider, messages: list[dict], timeout_seconds: float
) -> AsyncIterator[str]:
    client = AsyncOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key or "local",
        timeout=timeout_seconds,
    )
    extra = {}
    if provider.api_key == "local":
        extra["extra_body"] = {"chat_template_kwargs": {"thinking": False}}
    stream = await client.chat.completions.create(
        model=provider.model,
        messages=messages,
        max_tokens=200,
        stream=True,
        **extra,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


def canned_narration(canned_dir, image_hash: str) -> str:
    from .cells import load_canned

    data = load_canned(canned_dir, "narrations.json")
    if data is None:
        return ""
    return data.get(image_hash) or data.get("_generic", "")


async def narrate(
    detections: list[Detection],
    image_hash: str,
    settings: Settings,
) -> AsyncIterator[str]:
    messages = build_messages(detections)
    for provider in build_providers(settings):
        stream = stream_from_provider(provider, messages, settings.llm_timeout_seconds)
        try:
            first = await asyncio.wait_for(
                stream.__anext__(), settings.llm_timeout_seconds
            )
        except (asyncio.TimeoutError, StopAsyncIteration):
            continue
        except Exception:
            continue
        yield first
        try:
            async for chunk in stream:
                yield chunk
        except Exception:
            pass
        return
    cached = canned_narration(settings.canned_dir, image_hash)
    if cached:
        yield cached
