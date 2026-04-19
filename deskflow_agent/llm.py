from __future__ import annotations

from typing import Any

from deskflow_agent.config import GEMINI_API_KEY, GROQ_API_KEY, LLM_MODEL, LLM_PROVIDER


def _require_provider() -> None:
    if not LLM_PROVIDER:
        raise EnvironmentError(
            "No LLM API key found. Set GROQ_API_KEY or GEMINI_API_KEY in your .env file."
        )


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    json_mode: bool = False,
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> str:
    """
    Unified LLM call. Automatically routes to Groq or Gemini based on
    whichever API key is set in the environment.
    """
    _require_provider()
    if LLM_PROVIDER == "groq":
        return await _groq_chat(messages, json_mode=json_mode, temperature=temperature, max_tokens=max_tokens)
    return await _gemini_chat(messages, json_mode=json_mode, temperature=temperature, max_tokens=max_tokens)


async def _groq_chat(
    messages: list[dict[str, str]],
    *,
    json_mode: bool,
    temperature: float,
    max_tokens: int | None,
) -> str:
    from groq import AsyncGroq

    client = AsyncGroq(api_key=GROQ_API_KEY)
    kwargs: dict[str, Any] = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


async def _gemini_chat(
    messages: list[dict[str, str]],
    *,
    json_mode: bool,
    temperature: float,
    max_tokens: int | None,
) -> str:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)

    system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_content = "\n\n".join(m["content"] for m in messages if m["role"] == "user")

    generation_config: dict[str, Any] = {"temperature": temperature}
    if json_mode:
        generation_config["response_mime_type"] = "application/json"
    if max_tokens:
        generation_config["max_output_tokens"] = max_tokens

    model = genai.GenerativeModel(
        model_name=LLM_MODEL,
        system_instruction=system_prompt or None,
        generation_config=generation_config,
    )

    response = await model.generate_content_async(user_content)
    return response.text
