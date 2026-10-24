"""Send Gemini text requests through the Mubit gateway."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import aiohttp


async def send_text(
    *,
    api_key: str,
    model: str,
    reasoning: str,
    instructions: str,
    prompt: str,
    schema: dict[str, object] | None,
) -> tuple[str, str]:
    """Submit one request and return the answer and gateway request ID."""
    generation: dict[str, object] = {'thinkingConfig': {'thinkingLevel': reasoning.upper()}}
    if schema is not None:
        generation.update(responseMimeType='application/json', responseJsonSchema=schema)
    body = {
        'systemInstruction': {'parts': [{'text': instructions}]},
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': generation,
    }
    url = f'https://api.mubit.ai/gemini/v1beta/models/{quote(model, safe="")}:generateContent'
    try:
        async with (
            aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session,
            session.post(url, json=body, headers={'x-goog-api-key': api_key}, allow_redirects=False) as response,
        ):
            if response.status != HTTPStatus.OK:
                message = f'Mubit returned HTTP {response.status}. Check provider access, quota, and billing in Mubit.'
                raise RuntimeError(message)
            result = await response.json()
            request_id = response.headers.get('x-middleware-request-id', '')
    except TimeoutError as error:
        message = 'Mubit timed out after 300 seconds. Check the request before running it again.'
        raise RuntimeError(message) from error
    except aiohttp.ClientError as error:
        message = 'Could not complete the Mubit request. Check your connection and provider setup.'
        raise RuntimeError(message) from error
    return _read_text(result), request_id


def _read_text(result: object) -> str:
    """Read a complete answer, excluding internal thinking parts."""
    try:
        payload = cast('dict[str, Any]', result)
        candidate = payload['candidates'][0]
        if candidate.get('finishReason') != 'STOP':
            message = 'Mubit did not return a complete answer. Check the model response in Mubit Requests.'
            raise ValueError(message)
        parts = candidate['content']['parts']
        text = ''.join(part['text'] for part in parts if 'text' in part and not part.get('thought', False))
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        message = 'Mubit returned an invalid or blocked answer. Check the model response in Mubit Requests.'
        raise ValueError(message) from error
    if not text.strip():
        message = 'Mubit returned an empty answer. Check the model response in Mubit Requests.'
        raise ValueError(message)
    return text
