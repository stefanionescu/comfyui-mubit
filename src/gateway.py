"""Send model requests through Mubit."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast

import aiohttp

from .models import PROVIDERS

if TYPE_CHECKING:
    from .models import Model


def _build_body(
    model: Model,
    *,
    instructions: str,
    prompt: str,
    schema: dict[str, object] | None,
    images: list[str],
    audio: list[str],
) -> dict[str, object]:
    """Encode the selected provider's chat or Messages request. Only the OpenRouter and Gemini routes receive audio."""
    if model.provider == 'Anthropic':
        content = [{'type': 'text', 'text': prompt}] + [
            {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': data}} for data in images
        ]
        body: dict[str, object] = {
            'model': model.id,
            'system': instructions,
            'messages': [{'role': 'user', 'content': content}],
            'max_tokens': model.max_tokens,
        }
        output: dict[str, object] = {}
        if model.reasoning != 'default':
            output['effort'] = model.reasoning
        if schema is not None:
            output['format'] = {'type': 'json_schema', 'schema': schema}
        if output:
            body['output_config'] = output
        return body
    content = [
        {'type': 'text', 'text': prompt},
        *({'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{data}'}} for data in images),
        *({'type': 'input_audio', 'input_audio': {'data': data, 'format': 'wav'}} for data in audio),
    ]
    body = {
        'model': model.id,
        'messages': [{'role': 'system', 'content': instructions}, {'role': 'user', 'content': content}],
        'max_completion_tokens' if model.provider == 'OpenAI' else 'max_tokens': model.max_tokens,
    }
    if model.reasoning != 'default':
        if model.provider == 'OpenRouter':
            body['reasoning'] = {'effort': model.reasoning}
        else:
            body['reasoning_effort'] = model.reasoning
    if schema is not None:
        body['response_format'] = {
            'type': 'json_schema',
            'json_schema': {'name': 'answer', 'strict': True, 'schema': schema},
        }
    return body


async def send_text(
    *,
    api_key: str,
    model: Model,
    instructions: str,
    prompt: str,
    schema: dict[str, object] | None,
    images: list[str],
    audio: list[str],
) -> tuple[str, str]:
    """Submit one request and return its answer and Mubit request ID."""
    body = _build_body(model, instructions=instructions, prompt=prompt, schema=schema, images=images, audio=audio)
    path = '/messages' if model.provider == 'Anthropic' else '/chat/completions'
    url = f'https://api.mubit.ai{PROVIDERS[model.provider]}{path}'
    headers = {'Authorization': f'Bearer {api_key}'}
    if model.provider == 'Anthropic':
        headers['anthropic-version'] = '2023-06-01'
    try:
        async with (
            aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session,
            session.post(url, json=body, headers=headers, allow_redirects=False) as response,
        ):
            request_id = response.headers.get('x-middleware-request-id', '')
            if response.status != HTTPStatus.OK:
                message = f'Mubit returned HTTP {response.status}. Check the selected provider in Mubit.'
                if request_id:
                    message += f' Mubit request ID: {request_id}.'
                raise RuntimeError(message)
            result = await response.json()
    except TimeoutError as error:
        message = 'Mubit timed out after 300 seconds. Check the request before running it again.'
        raise RuntimeError(message) from error
    except aiohttp.ClientError as error:
        message = 'Could not complete the Mubit request. Check your connection and provider setup.'
        raise RuntimeError(message) from error
    return _read_text(result, model.provider), request_id


def _read_text(result: object, provider: str) -> str:
    """Read complete answer text from the selected provider's response."""
    try:
        payload = cast('dict[str, Any]', result)
        if provider == 'Anthropic':
            finished = payload['stop_reason'] in {'end_turn', 'stop_sequence'}
            text = ''.join(part['text'] for part in payload['content'] if part['type'] == 'text')
        else:
            choice = payload['choices'][0]
            finished = choice['finish_reason'] == 'stop'
            text = choice['message']['content']
    except (KeyError, IndexError, TypeError) as error:
        message = 'Mubit returned an invalid answer. Check the response in Mubit Requests.'
        raise ValueError(message) from error
    if not finished or not isinstance(text, str) or not text.strip():
        message = 'Mubit returned an incomplete, blocked, or empty answer. Check the response in Mubit Requests.'
        raise ValueError(message)
    return text
