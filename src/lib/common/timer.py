import datetime
from typing import Any, Callable


def timer(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that measures the time taken by a function to execute.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = datetime.datetime.now()
        result = func(*args, **kwargs)
        end = datetime.datetime.now()
        print(f"[{func.__name__}] Time elapsed: {end - start}")
        return result

    return wrapper
