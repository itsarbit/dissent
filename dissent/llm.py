import json
import re

from openai import AsyncOpenAI


def create_client(
    base_url: str | None = None, api_key: str | None = None
) -> AsyncOpenAI:
    kwargs = {}
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key
    return AsyncOpenAI(**kwargs)


async def chat_json(
    client: AsyncOpenAI,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.3,
) -> dict:
    """Send a chat request and parse the response as JSON.

    Works with models that support JSON mode and those that don't -
    falls back to extracting JSON from freeform text.
    """
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    content = response.choices[0].message.content or ""
    return _parse_json(content)


def _parse_json(content: str) -> dict:
    # Direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Extract from markdown code block
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Find outermost braces
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            pass

    return {"findings": []}
