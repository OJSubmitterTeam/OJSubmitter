import traceback
from functools import wraps
from typing import Any, Callable, Generic, Optional, TypeVar, Union

from PyQt6.QtWidgets import QWidget

from ..Typehint.basic import Callback, Function
from .Util.qt_tools import qt_dialog

_FT_R = TypeVar("_FT_R")


class WrapRunner(Generic[_FT_R]):
    def __init__(self, fn: Callable[..., _FT_R]) -> None:
        self.fn = fn

    def __call__(self, *args: Any, **kwds: Any) -> Union[_FT_R, Exception]:
        return self.run(*args, **kwds)

    def run(self, *args: Any, **kwargs: Any) -> Union[_FT_R, Exception]:
        try:
            return self.fn(*args, **kwargs)
        except Exception as e:
            return e


class GUIErrorHandler:

    def __init__(
        self,
        parent: QWidget,
        callback: Optional[Callback] = None,
        openTraceback: bool = False,
        display_dialog: bool = True,
    ) -> None:
        self.parent: QWidget = parent
        self.openTraceback: bool = openTraceback
        self.callback: Optional[Callback] = callback
        self.default_display_dialog = display_dialog

    def __call__(self, func: Function) -> Function:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self.display_dialog:
                    qt_dialog(
                        "Error",
                        f"{type(e).__name__}: {e}",
                        details=traceback.format_exc() if self.openTraceback else None,
                    )
                return e
            finally:
                if self.callback:
                    self.callback()

        return wrapper

    def fetch(
        self, func: Callable[..., _FT_R], display_dialog: Optional[bool] = None
    ) -> WrapRunner[_FT_R]:
        self.display_dialog = (
            self.default_display_dialog if display_dialog is None else display_dialog
        )
        return WrapRunner(self.__call__(func))

    def at_exit(self) -> None:
        pass
