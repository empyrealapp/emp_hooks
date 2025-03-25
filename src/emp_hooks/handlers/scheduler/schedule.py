from collections.abc import Callable

from .hooks import scheduled_hooks


def on_schedule(
    execution_frequency: int | str,
    execute_on_start: bool = False,
    identifier: str | None = None,
):
    def wrapper(func: Callable[[], None]):
        scheduled_hooks.add_scheduled_function(
            func,
            identifier or func.__name__,
            execution_frequency,
            execute_on_start,
        )
        return func

    return wrapper
