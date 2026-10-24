"""Generate text and structured answers through Mubit."""

from __future__ import annotations

import os
import json
from typing import cast, override

from comfy_api.latest import io

from ..gateway import send_text
from ..execution import wait_for_request


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
        text, request_id = await wait_for_request(
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
