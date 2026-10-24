# Verify

Evaluate a claim against text evidence and a policy using Banyan Sapling.
Set `SAPLING_ENDPOINT` in the ComfyUI server environment to your HTTPS inference URL.
If the deployment requires authentication, set its dedicated token in `SAPLING_API_KEY`.

## Inputs

| Input        | Behavior                                                    |
| ------------ | ----------------------------------------------------------- |
| `run_number` | Starts at zero. Change it to verify unchanged inputs again. |
| `policy`     | The rule that governs the claim.                            |
| `evidence`   | Source facts or an actual inspection of the relevant media. |
| `claim`      | The exact assertion to evaluate.                            |

## Outputs

| Output       | What it carries                                                          |
| ------------ | ------------------------------------------------------------------------ |
| `verdict`    | The exact calibrated status returned by Sapling.                         |
| `result`     | The complete response, including calibration metadata and probabilities. |
| `request_id` | The service's request ID when supplied.                                  |

The request ID remains empty when the service omits it.

Verdicts retain the service's exact meaning: `supported`, `violation`, `insufficient_information`,
`inconsistent_context` or `unsure`. The result includes calibration metadata and prediction sets.
Treat `unsure` as unresolved even when the raw label suggests support.

## Use

1. Write the requirement in `policy` and the observations in `evidence`.
2. Write the assertion to check in `claim`.
3. Connect outputs to **Preview as Text** and select **Run**.

For a wardrobe check, the policy can require a black button-down shirt. The evidence describes the candidate's
visible clothing, and the claim states whether that wardrobe requirement holds. A positive verdict about a defect
claim means the defect needs attention.

Sapling receives text. Inspect new images or video with a visual model first, then supply its actual observations.
Keep the evidence tied to the exact image or video timestamps under review.

Missing configuration, blank fields, service errors, and unrecognized statuses stop execution.
Requests time out after 300 seconds. **Stop** cancels the local HTTP task. Requests have no automatic retries.
