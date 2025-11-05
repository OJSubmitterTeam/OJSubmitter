from typing import List

from PyQt6.QtWidgets import QMessageBox, QWidget

from ..OJSubmitter.Interface.log_interface import (
    BaseLogger,
    CallbackFunction,
    LogLevels,
)


class GUILogger(BaseLogger):
    callbacks: List[CallbackFunction] = []

    def __init__(self, parent: QWidget) -> None:
        self.parent: QWidget = parent

    def notify(self, title: str, message: str, lvl: LogLevels) -> None:
        mapper = {
            LogLevels.LOG: QMessageBox.information,
            LogLevels.INFO: QMessageBox.information,
            LogLevels.WARN: QMessageBox.warning,
            LogLevels.ERROR: QMessageBox.critical,
            LogLevels.DEBUG: QMessageBox.information,
            LogLevels.TRACE: QMessageBox.critical,
            LogLevels.CRITICAL: QMessageBox.critical,
        }
        mapper[lvl](self.parent, title, message)

    def log(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.LOG)
        self.notify("Log", message, LogLevels.LOG)

    def info(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.INFO)
        self.notify("Info", message, LogLevels.INFO)

    def warn(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.WARN)
        self.notify("Warning", message, LogLevels.WARN)

    def error(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.ERROR)
        self.notify("Error", message, LogLevels.ERROR)

    def debug(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.DEBUG)
        self.notify("Debug", message, LogLevels.DEBUG)

    def trace(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.TRACE)
        self.notify("Trace", message, LogLevels.TRACE)

    def critical(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.CRITICAL)
        self.notify("Critical", message, LogLevels.CRITICAL)

    def set_callback(self, callback: CallbackFunction) -> None:
        BaseLogger.set_callback(self, callback)
