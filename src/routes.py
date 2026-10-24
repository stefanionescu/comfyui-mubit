"""Configure connections from the local ComfyUI page."""

from __future__ import annotations

import os
import json
from typing import cast
import asyncio
import ipaddress
from urllib.parse import urlsplit

from aiohttp import web

from .settings import read_status, save_connections

_HEADERS = {'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'}
_MAX_REQUEST_BYTES = 8192


def _require_owner(request: web.Request, *, is_write: bool, multi_user: bool) -> None:
    """Allow the direct local page to manage a single user's saved connections."""
    if request.remote is None or not ipaddress.ip_address(request.remote).is_loopback:
        raise web.HTTPForbidden(text='Open connection settings on the local ComfyUI computer.')
    target = urlsplit(f'{request.scheme}://{request.host}')
    if target.hostname not in {'localhost', '127.0.0.1', '::1'}:
        raise web.HTTPForbidden(text='Connection settings require a loopback address.')
    origin = request.headers.get('Origin')
    if origin and origin.rstrip('/') != f'{request.scheme}://{request.host}':
        raise web.HTTPForbidden(text='Connection settings require the same ComfyUI origin.')
    if request.headers.get('Sec-Fetch-Site') in {'cross-site', 'same-site'}:
        raise web.HTTPForbidden(text='Connection settings require the local ComfyUI page.')
    if is_write and (multi_user or request.headers.get('X-Mubit-Comfy') != '1'):
        raise web.HTTPForbidden(text='Connection changes require the local single-user settings panel.')


def register_routes(routes: web.RouteTableDef, *, multi_user: bool) -> None:
    """Register status and connection changes without exposing saved secrets."""

    async def status(request: web.Request) -> web.Response:
        """Describe connection sources to the local page."""
        _require_owner(request, is_write=False, multi_user=multi_user)
        result = await asyncio.to_thread(read_status, os.environ)
        return web.json_response(result | {'mutation_allowed': not multi_user}, headers=_HEADERS)

    async def save(request: web.Request) -> web.Response:
        """Apply text settings from the local panel and return their status."""
        _require_owner(request, is_write=True, multi_user=multi_user)
        if (
            request.content_type != 'application/json'
            or request.content_length is None
            or request.content_length > _MAX_REQUEST_BYTES
        ):
            raise web.HTTPBadRequest(text='Send connection settings as a JSON object of at most 8192 bytes.')
        try:
            document: object = await request.json()
        except json.JSONDecodeError as error:
            raise web.HTTPBadRequest(text='Connection settings must contain valid JSON.') from error
        if not isinstance(document, dict):
            raise web.HTTPBadRequest(text='Connection settings must be a JSON object.')
        fields = cast('dict[str, object]', document)
        if not all(isinstance(value, str) for value in fields.values()):
            raise web.HTTPBadRequest(text='Connection settings must be an object of text values.')
        try:
            result = await asyncio.to_thread(save_connections, cast('dict[str, str]', fields), os.environ)
        except ValueError as error:
            raise web.HTTPBadRequest(text=str(error)) from error
        return web.json_response(result | {'mutation_allowed': True}, headers=_HEADERS)

    routes.get('/mubit/settings')(status)
    routes.patch('/mubit/settings')(save)
