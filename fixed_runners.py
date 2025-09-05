"""
Восстановленный файл asyncio/runners.py
"""

import asyncio
import contextvars
import functools
import inspect
import signal
import threading
import warnings
from types import TracebackType
from typing import Any, Awaitable, Optional, TypeVar, Union

__all__ = ("Runner", "run")

T = TypeVar("T")


class Runner:
    """A context manager that controls the execution of asyncio coroutines."""

    def __init__(self, *, debug: Optional[bool] = None, loop_factory=None):
        self._state = _State.CREATED
        self._debug = debug
        self._loop_factory = loop_factory
        self._loop = None
        self._context = None
        self._interrupt_count = 0
        self._set_event_loop = False

    def __enter__(self):
        self._lazy_init()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the runner."""
        if self._state is not _State.CLOSED:
            try:
                loop = self._loop
                _cancel_all_tasks(loop)
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
            finally:
                if self._set_event_loop:
                    asyncio.set_event_loop(None)
                loop.close()
                self._loop = None
                self._state = _State.CLOSED

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """Return the event loop associated with the runner instance."""
        self._lazy_init()
        return self._loop

    def run(self, coro: Awaitable[T], *, context: Optional[contextvars.Context] = None) -> T:
        """Run a coroutine."""
        if not inspect.iscoroutine(coro) and not inspect.isawaitable(coro):
            raise ValueError("a coroutine was expected")

        if self._state is _State.CLOSED:
            raise RuntimeError("Runner is closed")

        if self._state is _State.INITIALIZED:
            # Reuse existing loop
            task = self._loop.create_task(coro, context=context)
        else:
            self._lazy_init()
            if context is None:
                context = self._context
            task = self._loop.create_task(coro, context=context)

        if self._loop.is_running():
            # Called from a running loop
            raise RuntimeError(
                "asyncio.run() cannot be called from a running event loop"
            )

        try:
            return self._loop.run_until_complete(task)
        except KeyboardInterrupt:
            # The main task was cancelled due to SIGINT.
            raise
        except SystemExit:
            raise
        except BaseException as exc:
            if task.done() and not task.cancelled():
                task.result()
            raise

    def _lazy_init(self):
        if self._state is _State.CLOSED:
            raise RuntimeError("Runner is closed")
        if self._state is _State.INITIALIZED:
            return
        if asyncio._get_running_loop() is not None:
            raise RuntimeError(
                "Runner.run() cannot be called from a running event loop"
            )
        self._set_event_loop = asyncio.get_event_loop_policy().get_event_loop() is None
        if self._loop_factory is None:
            self._loop = asyncio.new_event_loop()
        else:
            self._loop = self._loop_factory()
        if self._debug is not None:
            self._loop.set_debug(self._debug)
        self._context = contextvars.copy_context()
        asyncio.set_event_loop(self._loop)
        self._state = _State.INITIALIZED


class _State:
    CREATED = "CREATED"
    INITIALIZED = "INITIALIZED"
    CLOSED = "CLOSED"


def _cancel_all_tasks(loop):
    tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
    if not tasks:
        return
    for task in tasks:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })


def run(main: Awaitable[T], *, debug: Optional[bool] = None) -> T:
    """Execute the coroutine and return the result."""
    if asyncio._get_running_loop() is not None:
        raise RuntimeError(
            "asyncio.run() cannot be called from a running event loop"
        )

    with Runner(debug=debug) as runner:
        return runner.run(main)
