"""Generate text and structured answers through Mubit."""

from __future__ import annotations

import os
import json
from typing import TYPE_CHECKING, cast, override
import asyncio

from comfy_api.latest import io
from comfy_api_nodes.util import tensor_to_base64_string

from ..gateway import send_text
from ..execution import wait_for_request

if TYPE_CHECKING:
    from ..models import Model


def _encode_images(images: dict[str, io.Image.Type]) -> list[str]:
    """Encode each connected image in socket and batch order without resizing."""
    encoded: list[str] = []
    for batch in images.values():
        encoded.extend(tensor_to_base64_string(frame, total_pixels=None) for frame in batch)
    return encoded


class MubitAsk(io.ComfyNode):
    """Request text or structured JSON from a selected model through Mubit."""

    @classmethod
    @override
    def define_schema(cls) -> io.Schema:
        """Describe the request controls and returned values."""
        return io.Schema(
            node_id='MubitAsk',
            display_name='Ask',
            category='mubit',
            description='Ask the selected model about text or connected images through Mubit.',
            inputs=[
                io.Custom('MUBIT_MODEL').Input('model'),
                io.Int.Input(
                    'run_number',
                    default=0,
                    min=0,
                    max=2147483647,
                    tooltip='Change this number to send a fresh request with otherwise identical inputs.',
                ),
                io.Autogrow.Input(
                    'images',
                    template=io.Autogrow.TemplatePrefix(io.Image.Input('image'), prefix='image', min=0, max=100),
                    optional=True,
                    tooltip='Images in socket order. The selected model must support image inputs.',
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
        model: Model,
        run_number: int,
        instructions: str,
        prompt: str,
        json_schema: str = '',
        images: dict[str, io.Image.Type] | None = None,
    ) -> io.NodeOutput:
        """Validate inputs, make one request and parse requested JSON once."""
        del run_number
        api_key = os.environ.get('MUBIT_API_KEY', '').strip()
        if not api_key:
            message = 'Set MUBIT_API_KEY in the ComfyUI server environment and restart ComfyUI.'
            raise ValueError(message)
        if not instructions.strip() or not prompt.strip():
            message = 'Instructions and prompt must contain text.'
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
                model=model,
                instructions=instructions,
                prompt=prompt,
                schema=cast('dict[str, object] | None', schema),
                images=await asyncio.to_thread(_encode_images, images or {}),
            )
        )
        parsed = json.loads(text) if schema is not None else None
        return io.NodeOutput(text, parsed, request_id)
