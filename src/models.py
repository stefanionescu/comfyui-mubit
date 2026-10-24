"""Provider routes and the model settings shared by request nodes."""

from dataclasses import dataclass

PROVIDERS = {
    'OpenRouter': '/compat/openrouter/v1',
    'OpenAI': '/openai/v1',
    'Anthropic': '/anthropic/v1',
    'Gemini': '/gemini/v1beta/openai',
    'Groq': '/compat/groq/v1',
    'Together': '/compat/together/v1',
    'Mistral': '/compat/mistral/v1',
}


@dataclass(frozen=True)
class Model:
    """The provider, model ID, and generation settings for one request.

    Attributes:
        provider: The selected Mubit provider route.
        id: The provider's model ID.
        reasoning: The requested effort, or default to omit it.
        max_tokens: The output token limit.

    """

    provider: str
    id: str
    reasoning: str
    max_tokens: int
