"""Register the mubit nodes with ComfyUI."""

from __future__ import annotations

from typing import override

from server import PromptServer
from comfy.cli_args import args
from comfy_api.latest import ComfyExtension, io

from .src.routes import register_routes
from .src.nodes.ask import MubitAsk
from .src.nodes.model import MubitModel
from .src.nodes.verify import MubitVerify

WEB_DIRECTORY = './web'


class Extension(ComfyExtension):
    """Expose the mubit nodes in the node menu."""

    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        """Return the registered node classes."""
        register_routes(PromptServer.instance.routes, multi_user=args.multi_user)
        return [MubitModel, MubitAsk, MubitVerify]


async def comfy_entrypoint() -> Extension:
    """Return the extension through ComfyUI's native entry point."""
    return Extension()
