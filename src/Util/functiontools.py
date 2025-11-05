import threading
from typing import Any, Callable, Never, NoReturn, Optional, TypeVar

FE_R = TypeVar("FE_R")
FN_A = TypeVar("FN_A")


def closure(
    fnc: Callable[..., FE_R],
    /,
    *args: Any,
    **kwargs: Any,
) -> Callable[..., FE_R]:
    def wrapped(*_: Any, **__: Any) -> FE_R:
        return fnc(*args, **kwargs)

    return wrapped


def fetch_err(fnc: Callable[..., FE_R]) -> Optional[Exception]:
    try:
        fnc()
    except Exception as e:
        return e
    return None


def do_nothing(*args: Any, **kwargs: Any) -> Any:
    return


def ignore_args(
    fnc: Callable[..., FE_R],
) -> Callable[..., FE_R]:
    def wrapped(*_: Any, **__: Any) -> FE_R:
        return fnc()

    return wrapped


class Debounce:
    def __init__(self, milliseconds: float):
        self.seconds = milliseconds / 1000
        self.debounced: Optional[threading.Timer] = None

    def __call__(self, func: Callable[..., FE_R]) -> Callable[..., None]:
        def decorator(*args: Any, **kwargs: Any) -> None:
            if self.debounced is not None:
                self.debounced.cancel()
            self.debounced = threading.Timer(self.seconds, func, args, kwargs)
            self.debounced.start()

        return decorator


def debounce(func: Callable[..., FE_R], milliseconds: float) -> Callable[..., None]:
    debouncer = Debounce(milliseconds)
    return debouncer(func)


def assert_false(arg: Never) -> NoReturn:
    assert False, f"Unreachable code reached with argument: {arg}"


def default_choice(prompt: str, default: bool) -> bool:
    dm = {
        "y": True,
        "yes": True,
        "n": False,
        "no": False,
        "": default,
    }
    inp = input(prompt).strip().lower()
    if inp not in dm:
        raise ValueError(f"Invalid input: {inp}")
    return dm[inp]
