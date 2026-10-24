"""Define the mubit nodes and connect request cancellation to ComfyUI's Stop button."""

from __future__ import annotations

import os
import json
from typing import TYPE_CHECKING, cast, override
import asyncio
from urllib.parse import urlsplit

from comfy_api.latest import io
from comfy.model_management import throw_exception_if_processing_interrupted

from .gateway import send_text
from .sapling import verify_claim

if TYPE_CHECKING:
    from collections.abc import Coroutine


async def _wait_for_request[Result](work: Coroutine[object, object, Result]) -> Result:
    """Cancel the owned HTTP task when ComfyUI interrupts this execution."""
    task = asyncio.create_task(work)
    try:
        while not task.done():
            throw_exception_if_processing_interrupted()
            await asyncio.wait({task}, timeout=0.1)
        return await task
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


class MubitAsk(io.ComfyNode):
    """Generate text or structured JSON through the Mubit Gemini gateway."""

    @classmethod
    @override
    def define_schema(cls) -> io.Schema:
        """Describe the request controls and returned values."""
        return io.Schema(
            node_id='MubitAsk',
            display_name='Ask',
            category='mubit',
            description='Ask a Gemini model through Mubit. Credentials come from the server environment.',
            inputs=[
                io.Int.Input(
                    'run_number',
                    default=0,
                    min=0,
                    max=2147483647,
                    tooltip='Change this number to send a fresh request with otherwise identical inputs.',
                ),
                io.Combo.Input('reasoning', options=['low', 'medium', 'high'], default='high'),
                io.String.Input(
                    'model', default='gemini-4-argon', tooltip='A model available through your Mubit account.'
                ),
                io.String.Input(
                    'instructions',
                    multiline=True,
                    dynamic_prompts=False,
                    default='Use only the supplied facts. Keep the answer concise.',
                    tooltip='Stable instructions describing the task and its constraints.',
                ),
                io.String.Input(
                    'prompt',
                    multiline=True,
                    dynamic_prompts=False,
                    tooltip='The current request and source facts.',
                ),
                io.String.Input(
                    'json_schema',
                    multiline=True,
                    optional=True,
                    default='',
                    dynamic_prompts=False,
                    tooltip='Optional JSON Schema object. Leave empty for a plain text answer.',
                ),
            ],
            outputs=[io.String.Output('text'), io.AnyType.Output('json'), io.String.Output('request_id')],
        )

    @classmethod
    @override
    async def execute(  # pyright: ignore[reportIncompatibleMethodOverride] # reason: ComfyUI awaits schema-defined inputs.
        cls,
        run_number: int,
        reasoning: str,
        model: str,
        instructions: str,
        prompt: str,
        json_schema: str = '',
    ) -> io.NodeOutput:
        """Validate inputs, make one request and parse requested JSON once."""
        del run_number
        api_key = os.environ.get('MUBIT_API_KEY', '').strip()
        if not api_key:
            message = 'Set MUBIT_API_KEY in the ComfyUI server environment and restart ComfyUI.'
            raise ValueError(message)
        if not all(value.strip() for value in (model, instructions, prompt)):
            message = 'Model, instructions and prompt must contain text.'
            raise ValueError(message)
        if reasoning not in {'low', 'medium', 'high'}:
            message = 'Reasoning must be low, medium or high.'
            raise ValueError(message)
        schema = None
        if json_schema.strip():
            schema = json.loads(json_schema)
            if not isinstance(schema, dict):
                message = 'JSON Schema must be a JSON object.'
                raise ValueError(message)
        text, request_id = await _wait_for_request(
            send_text(
                api_key=api_key,
                model=model.strip(),
                reasoning=reasoning,
                instructions=instructions,
                prompt=prompt,
                schema=cast('dict[str, object] | None', schema),
            )
        )
        parsed = json.loads(text) if schema is not None else None
        return io.NodeOutput(text, parsed, request_id)


class MubitVerify(io.ComfyNode):
    """Evaluate the relation between supplied text evidence, policy, and claim."""

    @classmethod
    @override
    def define_schema(cls) -> io.Schema:
        """Describe the verification inputs and calibrated outputs."""
        return io.Schema(
            node_id='MubitVerify',
            display_name='Verify',
            category='mubit',
            description='Verify text evidence with Banyan Sapling. Media requires an actual inspection first.',
            inputs=[
                io.Int.Input(
                    'run_number',
                    default=0,
                    min=0,
                    max=2147483647,
                    tooltip='Change this number to verify unchanged inputs again.',
                ),
                io.String.Input(
                    'policy',
                    multiline=True,
                    dynamic_prompts=False,
                    default='Every factual assertion in the claim must follow from the evidence.',
                    tooltip='The rule against which to evaluate the claim.',
                ),
                io.String.Input(
                    'evidence',
                    multiline=True,
                    dynamic_prompts=False,
                    tooltip='Source facts, or an actual observation of the generated media.',
                ),
                io.String.Input(
                    'claim',
                    multiline=True,
                    dynamic_prompts=False,
                    tooltip='The exact assertion to evaluate under the policy.',
                ),
            ],
            outputs=[io.String.Output('verdict'), io.AnyType.Output('result'), io.String.Output('request_id')],
        )

    @classmethod
    @override
    async def execute(  # pyright: ignore[reportIncompatibleMethodOverride] # reason: ComfyUI awaits schema-defined inputs.
        cls,
        run_number: int,
        policy: str,
        evidence: str,
        claim: str,
    ) -> io.NodeOutput:
        """Send text evidence and return the exact calibrated verdict."""
        del run_number
        endpoint = os.environ.get('SAPLING_ENDPOINT', '').strip()
        address = urlsplit(endpoint)
        if address.scheme != 'https' or not address.hostname or address.username or address.query or address.fragment:
            message = 'Set SAPLING_ENDPOINT to the HTTPS inference URL, without credentials, query or fragment.'
            raise ValueError(message)
        if not all(value.strip() for value in (policy, evidence, claim)):
            message = 'Policy, evidence and claim must contain text.'
            raise ValueError(message)
        verdict, result, request_id = await _wait_for_request(
            verify_claim(
                endpoint=endpoint,
                api_key=os.environ.get('SAPLING_API_KEY', '').strip(),
                policy=policy,
                evidence=evidence,
                claim=claim,
            )
        )
        return io.NodeOutput(verdict, result, request_id)
