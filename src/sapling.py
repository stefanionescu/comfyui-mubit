"""Verify a policy, evidence and claim with the deployed Banyan Sapling handler."""

from __future__ import annotations

from http import HTTPStatus
from typing import cast

import aiohttp


async def verify_claim(
    *,
    endpoint: str,
    api_key: str,
    policy: str,
    evidence: str,
    claim: str,
) -> tuple[str, dict[str, object], str]:
    """Submit one verification and preserve its calibrated result and request ID."""
    headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}
    body = {'inputs': {'policy': policy, 'evidence': evidence, 'claim': claim}}
    try:
        async with (
            aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session,
            session.post(endpoint, json=body, headers=headers, allow_redirects=False) as response,
        ):
            if response.status != HTTPStatus.OK:
                message = f'Sapling returned HTTP {response.status}. Check the endpoint and its access settings.'
                raise RuntimeError(message)
            result = await response.json()
            request_id = response.headers.get('x-request-id', '')
    except TimeoutError as error:
        message = 'Sapling timed out after 300 seconds. Check the endpoint before running it again.'
        raise RuntimeError(message) from error
    except aiohttp.ClientError as error:
        message = 'Could not complete verification. Check your connection and the Sapling endpoint.'
        raise RuntimeError(message) from error
    verdict, full_result = read_verification(result)
    return verdict, full_result, request_id


def read_verification(result: object) -> tuple[str, dict[str, object]]:
    """Read the calibrated status without reducing or replacing the service's verdict."""
    if not isinstance(result, dict) or 'error' in result:
        message = 'Sapling returned an invalid result or an error. Check the endpoint deployment.'
        raise ValueError(message)
    full_result = cast('dict[str, object]', result)
    verdict = full_result.get('status')
    if not isinstance(verdict, str) or verdict not in {
        'supported',
        'violation',
        'insufficient_information',
        'inconsistent_context',
        'unsure',
    }:
        message = 'Sapling returned no recognized calibrated status. Check the endpoint deployment.'
        raise ValueError(message)
    return verdict, full_result
