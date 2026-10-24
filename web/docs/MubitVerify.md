# Verify

Check a claim against text evidence and a policy using Banyan Sapling.
Set `SAPLING_ENDPOINT` to your HTTPS inference URL. Set `SAPLING_API_KEY` if the deployment requires a token.

## Inputs

| Input        | Behavior                                       |
| ------------ | ---------------------------------------------- |
| `run_number` | Change it to verify unchanged inputs again.    |
| `policy`     | The rule the claim must satisfy.               |
| `evidence`   | Source facts or current observations from Ask. |
| `claim`      | The exact assertion to check.                  |

## Outputs

| Output       | What it carries                                                         |
| ------------ | ----------------------------------------------------------------------- |
| `verdict`    | The service's calibrated status.                                        |
| `result`     | The complete response, including probabilities and calibration details. |
| `request_id` | The service's request ID when supplied; otherwise an empty string.      |

## Use

1. Write the policy and claim.
2. Connect source facts or the current image observations to evidence.
3. Connect outputs to Preview as Text and select Run.

Verify returns `supported`, `violation`, `insufficient_information`, `inconsistent_context`, or `unsure`.
Support for a positive requirement supports that requirement; support for a defect claim means the defect needs attention.
Keep uncertain results unresolved. The raw label does not replace the calibrated status.

Verify receives text evidence. Connect images to Ask first for media observations.
Errors stop execution. Requests time out after 300 seconds without automatic retries.
Stop cancels the local HTTP task.
