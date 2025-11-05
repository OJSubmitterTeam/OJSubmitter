import abc
from typing import Callable, Optional

from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QMainWindow, QWidget

from .UI_main import Ui_MainWindow


class BasicWindow(Ui_MainWindow, QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None):
        super(Ui_MainWindow, self).__init__(parent)
        super(BasicWindow, self).__init__(parent)
        self.setupUi(self)  # type: ignore[no-untyped-call]
        self._keyPressEventCallback: Optional[Callable[[QKeyEvent], None]] = None
        self._keyReleaseEventCallback: Optional[Callable[[QKeyEvent], None]] = None

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        (
            self._keyPressEventCallback
            if self._keyPressEventCallback is not None
            else super().keyPressEvent
        )(a0)

    def setKeyPressEventCallback(self, callback: Callable[[QKeyEvent], None]) -> None:
        self._keyPressEventCallback = callback

    def keyReleaseEvent(self, a0: QKeyEvent) -> None:
        (
            self._keyReleaseEventCallback
            if self._keyReleaseEventCallback is not None
            else super().keyReleaseEvent
        )(a0)

    def setKeyReleaseEventCallback(self, callback: Callable[[QKeyEvent], None]) -> None:
        self._keyReleaseEventCallback = callback


class LogicFrame(abc.ABC):
    @abc.abstractmethod
    def __init__(self, window: BasicWindow):
        self.window: BasicWindow = window

    @abc.abstractmethod
    def at_entry(self) -> None:
        pass

    @abc.abstractmethod
    def at_exit(self) -> None:
        pass


__all__ = ["BasicWindow", "LogicFrame"]
