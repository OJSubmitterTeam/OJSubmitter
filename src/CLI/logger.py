from typing import List, TypeAlias

from colorama import init as colorama_init

from ..OJSubmitter.Interface.log_interface import (
    BaseLogger,
    CallbackFunction,
    LogLevels,
    LogPackage,
    UnionLogLevel,
)
from .Util.color_print import cprint

LL: TypeAlias = LogLevels

colorama_init()


def cpprint(lp: LogPackage) -> None:
    cprint(lp["msg"], color=lp["color"])


class CLILogger(BaseLogger):
    callbacks: List[CallbackFunction] = []

    def emit(self, msg: str, source: str, lvl: UnionLogLevel, color: str = "") -> None:
        BaseLogger.emit(self, msg, source, lvl, color)

    def log(self, message: str, source: str) -> None:
        cpprint(self.template(source, LL.LOG, message))

    def info(self, message: str, source: str) -> None:
        cpprint(self.template(source, LL.INFO, message))

    def warn(self, message: str, source: str) -> None:
        cpprint(self.template(source, LL.WARN, message))

    def error(self, message: str, source: str) -> None:
        cpprint(self.template(source, LL.ERROR, message))

    def debug(self, message: str, source: str) -> None:
        cpprint(self.template(source, LL.DEBUG, message))

    def trace(self, message: str, source: str) -> None:
        cpprint(self.template(source, LL.TRACE, message))

    def critical(self, message: str, source: str) -> None:
        cpprint(self.template(source, LL.CRITICAL, message))

    def set_callback(self, callback: CallbackFunction) -> None:
        self.callbacks.append(callback)


logger = CLILogger()
