# Ask

Send one text request through the Mubit Gemini gateway.
Set `MUBIT_API_KEY` in the ComfyUI server environment and connect a Gemini provider in Mubit.

## Inputs

| Input          | Behavior                                                                                |
| -------------- | --------------------------------------------------------------------------------------- |
| `run_number`   | Starts at zero. Change it to request another execution with otherwise identical inputs. |
| `reasoning`    | Low, medium or high. Defaults to high.                                                  |
| `model`        | Model ID available to your Mubit account. Defaults to `gemini-4-argon`.                 |
| `instructions` | Stable task instructions, sent as the system instruction.                               |
| `prompt`       | Current request and source facts, sent as user content.                                 |
| `json_schema`  | Optional JSON Schema object. Leave empty for text.                                      |

## Outputs

| Output       | What it carries                               |
| ------------ | --------------------------------------------- |
| `text`       | The complete answer text.                     |
| `json`       | The parsed answer when a schema was supplied. |
| `request_id` | The actual Mubit request ID.                  |

Plain text requests return `None` on the JSON output. Connect any output to **Preview as Text** to inspect it.

## Use

1. Write the task in `instructions` and the current facts in `prompt`.
2. Connect the outputs to **Preview as Text** or the next workflow step.
3. Select **Run**. Change `run_number` to send the same request again.

For a structured answer, use a schema such as:

```json
{
    "type": "object",
    "properties": {
        "script": { "type": "string" }
    },
    "required": ["script"],
    "additionalProperties": false
}
```

Missing configuration, blank required inputs and invalid schema JSON fail before submission.
An incomplete, blocked, or malformed answer stops execution. Requests time out after 300 seconds.
**Stop** cancels the local HTTP task. Requests have no automatic retries.
