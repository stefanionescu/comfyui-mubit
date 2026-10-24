# Model

Choose a provider and model for Ask. Connect your provider in Mubit and set `MUBIT_API_KEY` on the ComfyUI server.

## Inputs

| Input        | Behavior                                                                        |
| ------------ | ------------------------------------------------------------------------------- |
| `provider`   | The connected provider. Starts on OpenRouter.                                   |
| `model`      | Any chat model ID served by that provider.                                      |
| `reasoning`  | Use default to omit the effort setting, or choose an effort the model supports. |
| `max_tokens` | The output token limit, including reasoning where the provider counts it.       |

## Outputs

| Output  | What it carries               |
| ------- | ----------------------------- |
| `model` | The settings consumed by Ask. |

## Use

1. Choose a provider and enter its model ID.
2. Connect the output to one or more Ask nodes.
3. Choose a model that supports the images, schema, and reasoning your task uses.

Model selects settings without making an inference request. Provider access and supported parameters depend on your account and model.
