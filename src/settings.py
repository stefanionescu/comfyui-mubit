"""Save connection settings outside ComfyUI's public folders."""

from __future__ import annotations

import os
import sys
import json
from typing import TYPE_CHECKING, cast
from pathlib import Path
import tempfile
import threading
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Mapping

_VARIABLES = {
    'api_key': 'MUBIT_API_KEY',
    'sapling_endpoint': 'SAPLING_ENDPOINT',
    'sapling_api_key': 'SAPLING_API_KEY',
}
_MAX_SETTINGS_BYTES = 8192
_MAX_FIELD_CHARACTERS = 2048
# Settings writes share one file; the lock preserves fields across section saves.
_write_lock = threading.Lock()


def _settings_file(environ: Mapping[str, str]) -> Path:
    """Locate the connection file in the current user's application settings."""
    if sys.platform == 'darwin':
        directory = Path.home() / 'Library' / 'Application Support' / 'MubitComfyUI'
    elif sys.platform == 'win32':
        directory = Path(environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))) / 'MubitComfyUI'
    else:
        directory = Path(environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'mubit-comfy'
    return directory / 'settings.json'


def _read_saved(environ: Mapping[str, str]) -> dict[str, str]:
    """Read saved fields without creating a directory or exposing their values."""
    path = _settings_file(environ)
    if not path.exists():
        return {}
    if path.stat().st_size > _MAX_SETTINGS_BYTES:
        message = 'The saved Mubit connection file exceeds 8192 bytes.'
        raise ValueError(message)
    document: object = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(document, dict):
        message = 'The saved Mubit connection file must contain an object.'
        raise TypeError(message)
    fields = cast('dict[str, object]', document)
    if fields.keys() - _VARIABLES.keys():
        message = 'The saved Mubit connection file has unknown settings.'
        raise ValueError(message)
    if not all(isinstance(value, str) for value in fields.values()):
        message = 'Saved Mubit connection settings must contain text.'
        raise TypeError(message)
    return cast('dict[str, str]', fields)


def read_connections(environ: Mapping[str, str]) -> dict[str, str]:
    """Read effective connections, with server environment values taking precedence."""
    saved = _read_saved(environ)
    connections: dict[str, str] = {}
    for name, variable in _VARIABLES.items():
        connections[name] = environ.get(variable, saved.get(name, '')).strip()
    return connections


def read_status(environ: Mapping[str, str]) -> dict[str, object]:
    """Return connection sources and the endpoint, without returning any key."""
    saved = _read_saved(environ)
    sources = {
        name: 'environment' if variable in environ else 'saved' if saved.get(name) else 'missing'
        for name, variable in _VARIABLES.items()
    }
    endpoint = environ.get(_VARIABLES['sapling_endpoint'], saved.get('sapling_endpoint', '')).strip()
    return {'sources': sources, 'sapling_endpoint': endpoint}


def save_connections(changes: Mapping[str, str], environ: Mapping[str, str]) -> dict[str, object]:
    """Save supplied connection fields; empty values clear their saved setting."""
    if changes.keys() - _VARIABLES.keys() or any(len(value) > _MAX_FIELD_CHARACTERS for value in changes.values()):
        message = 'Use the named Mubit connection fields, with at most 2048 characters each.'
        raise ValueError(message)
    endpoint = changes.get('sapling_endpoint', '').strip()
    if endpoint:
        address = urlsplit(endpoint)
        if address.scheme != 'https' or not address.hostname or address.username or address.query or address.fragment:
            message = 'Use an HTTPS Sapling endpoint without credentials, query or fragment.'
            raise ValueError(message)
    with _write_lock:
        saved = _read_saved(environ)
        for name, value in changes.items():
            if value.strip():
                saved[name] = value.strip()
            else:
                saved.pop(name, None)
        _write_connections(saved, environ)
    return read_status(environ)


def _write_connections(saved: dict[str, str], environ: Mapping[str, str]) -> None:
    """Replace the saved connection file through an owner-only temporary file."""
    path = _settings_file(environ)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, name = tempfile.mkstemp(prefix='.mubit-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
            output.write(json.dumps(saved) + '\n')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
