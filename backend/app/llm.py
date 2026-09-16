"""Minimal LLM client for structured model calls.

Speaks the OpenAI-compatible chat-completions protocol, so it works with
OpenRouter out of the box and with any OpenAI-compatible server (for example
a local Ollama instance) via LLM_BASE_URL. The scoring prompts describe what
a correct result looks like (the rubric and the cv-rubric skill); this module
only handles transport and parsing.
"""

import json
import os

import httpx

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4.1-mini"
DEFAULT_TIMEOUT = 120


class LLMError(Exception):
    """Raised when a model call fails or returns unusable output."""


def load_env(path: str | None = None) -> None:
    """Load KEY=VALUE pairs from the project .env without overriding the environment."""
    target = path or os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if not os.path.isfile(target):
        return
    with open(target, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def base_url() -> str:
    return os.environ.get("LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def model_name() -> str:
    return os.environ.get("LLM_MODEL", DEFAULT_MODEL)


def api_key() -> str | None:
    """Auth key for the configured endpoint.

    LLM_API_KEY always wins. The documented OPENROUTER_API_KEY is only used
    against the OpenRouter default, so a custom server never receives it.
    """
    explicit = os.environ.get("LLM_API_KEY")
    if explicit:
        return explicit
    if base_url() == DEFAULT_BASE_URL:
        return os.environ.get("OPENROUTER_API_KEY")
    return None


def structured_call(system: str, user: str, schema: dict) -> dict:
    """Run one chat completion with Structured Outputs and return the parsed JSON."""
    load_env()
    key = api_key()
    if not key and base_url() == DEFAULT_BASE_URL:
        raise LLMError("OPENROUTER_API_KEY is not set.")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    body = {
        "model": model_name(),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "jobfit_result",
                "strict": True,
                "schema": schema,
            },
        },
    }
    try:
        response = httpx.post(
            f"{base_url()}/chat/completions",
            headers=headers,
            json=body,
            timeout=float(os.environ.get("LLM_TIMEOUT", DEFAULT_TIMEOUT)),
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
        raise LLMError(f"Model call failed: {exc}") from exc