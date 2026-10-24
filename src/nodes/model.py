"""Choose a provider and model for Mubit requests."""

from typing import override

from comfy_api.latest import io

from ..models import PROVIDERS, Model


class MubitModel(io.ComfyNode):
    """Share one model selection between request nodes."""

    @classmethod
    @override
    def define_schema(cls) -> io.Schema:
        """Describe the provider, model ID, and generation controls."""
        return io.Schema(
            node_id='MubitModel',
            display_name='Model',
            category='mubit',
            description='Choose a connected provider and any model ID that provider serves.',
            inputs=[
                io.Combo.Input('provider', options=list(PROVIDERS), default='OpenRouter'),
                io.String.Input('model', tooltip='The exact model ID from the selected provider.'),
                io.Combo.Input(
                    'reasoning',
                    options=['default', 'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max'],
                    default='default',
                    tooltip='Use default to keep the model default. Other choices require model support.',
                ),
                io.Int.Input('max_tokens', default=8192, min=1, max=2147483647),
            ],
            outputs=[io.Custom('MUBIT_MODEL').Output('model')],
        )

    @classmethod
    @override
    def execute(  # pyright: ignore[reportIncompatibleMethodOverride] # reason: ComfyUI calls schema-defined inputs.
        cls, provider: str, model: str, reasoning: str, max_tokens: int
    ) -> io.NodeOutput:
        """Return the chosen settings without submitting a request."""
        model = model.strip()
        if not model:
            message = 'Enter a model ID from the selected provider.'
            raise ValueError(message)
        return io.NodeOutput(Model(provider, model, reasoning, max_tokens))
