"""Register the mubit nodes with ComfyUI."""

from __future__ import annotations

from typing import override

from comfy_api.latest import ComfyExtension, io

from .src.nodes import MubitAsk, MubitVerify


class Extension(ComfyExtension):
    """Expose the mubit nodes in the node menu."""

    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        """Return the registered node classes."""
        return [MubitAsk, MubitVerify]


async def comfy_entrypoint() -> Extension:
    """Return the extension through ComfyUI's native entry point."""
    return Extension()
