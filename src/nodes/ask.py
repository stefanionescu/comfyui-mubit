"""Generate text and structured answers through Mubit."""

from __future__ import annotations

from io import BytesIO
import os
import json
import wave
import base64
from typing import TYPE_CHECKING, cast, override
import asyncio

from comfy_api.latest import io
from comfy_api_nodes.util import tensor_to_base64_string

from ..models import AUDIO_PROVIDERS
from ..gateway import send_text
from ..settings import read_connections
from ..execution import wait_for_request

if TYPE_CHECKING:
    from comfy_api.latest import Input

    from ..models import Model


def _encode_images(images: dict[str, io.Image.Type]) -> list[str]:
    """Encode each connected image in socket and batch order without resizing."""
    encoded: list[str] = []
    for batch in images.values():
        encoded.extend(tensor_to_base64_string(frame, total_pixels=None) for frame in batch)
    return encoded


def _encode_audio(audio: Input.Audio) -> list[str]:
    """Encode each clip of the audio batch as one complete Waveform Audio File (WAV).

    The file holds 16-bit pulse-code modulation (PCM) samples, with the clip's own channels and sample rate.
    """
    encoded: list[str] = []
    for waveform in audio['waveform']:
        samples = (waveform.clamp(-1, 1) * 32767).round().short().transpose(0, 1).contiguous().cpu()
        buffer = BytesIO()
        with wave.open(buffer, 'wb') as output:
            output.setnchannels(samples.shape[1])
            output.setsampwidth(2)
            output.setframerate(audio['sample_rate'])
            output.writeframes(samples.numpy().tobytes())
        encoded.append(base64.b64encode(buffer.getvalue()).decode('ascii'))
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
            description='Ask the selected model about text, connected images, or audio through Mubit.',
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
                io.Audio.Input(
                    'audio',
                    optional=True,
                    tooltip=(
                        'Speech or sound, sent as one complete WAV file. Needs OpenRouter or Gemini, and a model that '
                        'hears audio.'
                    ),
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
        audio: Input.Audio | None = None,
    ) -> io.NodeOutput:
        """Validate inputs, make one request and parse requested JSON once."""
        del run_number
        api_key = read_connections(os.environ)['api_key']
        if not api_key:
            message = 'Save a Mubit API key in connection settings, or set MUBIT_API_KEY in the server environment.'
            raise ValueError(message)
        if not instructions.strip() or not prompt.strip():
            message = 'Instructions and prompt must contain text.'
            raise ValueError(message)
        if audio is not None and model.provider not in AUDIO_PROVIDERS:
            message = (
                'Audio input works with the OpenRouter and Gemini providers. Select one of them on Model, or '
                'disconnect the audio.'
            )
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
                audio=await asyncio.to_thread(_encode_audio, audio) if audio is not None else [],
            )
        )
        parsed = json.loads(text) if schema is not None else None
        return io.NodeOutput(text, parsed, request_id)
