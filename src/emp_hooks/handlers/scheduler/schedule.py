from collections.abc import Callable

from .hooks import scheduled_hooks


def on_schedule(
    execution_frequency: int | str,
    execute_on_start: bool = False,
    identifier: str | None = None,
):
    """
    Decorator to register a function to be called at a specific interval or cron schedule.

    Args:
        execution_frequency (int | str): The frequency at which the function should be executed or a cron string.
        execute_on_start (bool, optional): If True, the function will be executed immediately upon registration. Defaults to False.
        identifier (str | None, optional): An optional identifier for the scheduled function. If not provided, the function's name will be used.

    Returns:
        Callable: A decorator that registers the function to be called at the specified interval or cron schedule.
    """

    def wrapper(func: Callable[[], None]):
        scheduled_hooks.add_scheduled_function(
            func,
            identifier or func.__name__,
            execution_frequency,
            execute_on_start,
        )
        return func

    return wrapper
