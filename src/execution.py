"""Connect owned requests to ComfyUI cancellation."""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio

from comfy.model_management import throw_exception_if_processing_interrupted

if TYPE_CHECKING:
    from collections.abc import Coroutine


async def wait_for_request[Result](work: Coroutine[object, object, Result]) -> Result:
    """Cancel the owned HTTP task when ComfyUI interrupts this execution."""
    task = asyncio.create_task(work)
    try:
        while not task.done():
            throw_exception_if_processing_interrupted()
            await asyncio.wait({task}, timeout=0.1)
        return await task
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
