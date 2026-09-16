"""Minimal OpenRouter client for structured model calls.

The scoring prompts describe what a correct result looks like (the rubric and
the cv-rubric skill); this module only handles transport and parsing.
"""

import json
import os

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4.1-mini"


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


def model_name() -> str:
    return os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)


def structured_call(system: str, user: str, schema: dict) -> dict:
    """Run one chat completion with Structured Outputs and return the parsed JSON."""
    load_env()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise LLMError("OPENROUTER_API_KEY is not set.")
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
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout=120,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
        raise LLMError(f"Model call failed: {exc}") from exc