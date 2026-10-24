# Ask

Ask the selected model about text or connected images through Mubit.
Set `MUBIT_API_KEY` in the server environment and connect Model.

## Inputs

| Input          | Behavior                                                                                              |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| `model`        | Provider and model settings from Model.                                                               |
| `run_number`   | Change it to submit unchanged inputs again.                                                           |
| `images`       | Optional image sockets. Each connection adds another socket. Images keep their size and socket order. |
| `instructions` | Stable instructions for the task.                                                                     |
| `prompt`       | The current request and source facts.                                                                 |
| `json_schema`  | Optional JSON Schema object for a structured answer.                                                  |

## Outputs

| Output       | What it carries                                               |
| ------------ | ------------------------------------------------------------- |
| `text`       | The complete answer.                                          |
| `json`       | The parsed answer when a schema was supplied; otherwise None. |
| `request_id` | The Mubit request ID when supplied.                           |

## Use

1. Connect Model and write the task instructions and prompt.
2. For an image task, connect Load Image outputs in the order described by the prompt.
3. Connect the answer to Preview as Text or the next workflow step, then select Run.

Each image in a connected batch follows the other images from that socket. Choose a model with image support.
For a comparison, describe the first image as the reference and the second as the candidate.

For a structured answer, supply a schema such as:

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

Errors stop execution. Incomplete, blocked, or empty answers fail.
Requests time out after 300 seconds without automatic retries. Stop cancels the local HTTP task.
HTTP errors include the Mubit request ID when supplied.
