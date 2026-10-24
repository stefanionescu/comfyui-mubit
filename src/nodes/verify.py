"""Check claims against evidence with Sapling."""

from __future__ import annotations

import os
from typing import override
from urllib.parse import urlsplit

from comfy_api.latest import io

from ..sapling import verify_claim
from ..settings import read_connections
from ..execution import wait_for_request


class MubitVerify(io.ComfyNode):
    """Evaluate the relation between supplied text evidence, policy, and claim."""

    @classmethod
    @override
    def define_schema(cls) -> io.Schema:
        """Describe the verification inputs and calibrated outputs."""
        return io.Schema(
            node_id='MubitVerify',
            display_name='Verify',
            category='mubit',
            description='Verify text evidence with Banyan Sapling. Media requires an actual inspection first.',
            inputs=[
                io.Int.Input(
                    'run_number',
                    default=0,
                    min=0,
                    max=2147483647,
                    tooltip='Change this number to verify unchanged inputs again.',
                ),
                io.String.Input(
                    'policy',
                    multiline=True,
                    dynamic_prompts=False,
                    default='Every factual assertion in the claim must follow from the evidence.',
                    tooltip='The rule against which to evaluate the claim.',
                ),
                io.String.Input(
                    'evidence',
                    multiline=True,
                    dynamic_prompts=False,
                    tooltip='Source facts, or an actual observation of the generated media.',
                ),
                io.String.Input(
                    'claim',
                    multiline=True,
                    dynamic_prompts=False,
                    tooltip='The exact assertion to evaluate under the policy.',
                ),
            ],
            outputs=[io.String.Output('verdict'), io.AnyType.Output('result'), io.String.Output('request_id')],
        )

    @classmethod
    @override
    async def execute(  # pyright: ignore[reportIncompatibleMethodOverride] # reason: ComfyUI awaits schema-defined inputs.
        cls,
        run_number: int,
        policy: str,
        evidence: str,
        claim: str,
    ) -> io.NodeOutput:
        """Send text evidence and return the exact calibrated verdict."""
        del run_number
        connections = read_connections(os.environ)
        endpoint = connections['sapling_endpoint']
        address = urlsplit(endpoint)
        if (
            address.scheme != 'https'
            or not address.hostname
            or address.username is not None
            or address.query
            or address.fragment
        ):
            message = 'Set SAPLING_ENDPOINT to the HTTPS inference URL, without credentials, query or fragment.'
            raise ValueError(message)
        if not all(value.strip() for value in (policy, evidence, claim)):
            message = 'Policy, evidence and claim must contain text.'
            raise ValueError(message)
        verdict, result, request_id = await wait_for_request(
            verify_claim(
                endpoint=endpoint,
                api_key=connections['sapling_api_key'],
                policy=policy,
                evidence=evidence,
                claim=claim,
            )
        )
        return io.NodeOutput(verdict, result, request_id)
