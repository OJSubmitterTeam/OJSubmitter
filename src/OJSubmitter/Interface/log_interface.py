import enum
import os
import threading
import time
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Protocol,
    TypeAlias,
    TypedDict,
    Union,
)

from colorama import Fore

from ...Typehint.basic import Function

LogLevelLiteral = Literal["LOG", "INF", "WRN", "ERR", "DBG", "TRC", "CRT"]


class LogLevels(enum.StrEnum):
    LOG = "LOG"
    INFO = "INF"
    WARN = "WRN"
    ERROR = "ERR"
    DEBUG = "DBG"
    TRACE = "TRC"
    CRITICAL = "CRT"

    @staticmethod
    def from_str(level: LogLevelLiteral) -> "LogLevels":
        return {
            "LOG": LogLevels.LOG,
            "INF": LogLevels.INFO,
            "WRN": LogLevels.WARN,
            "ERR": LogLevels.ERROR,
            "DBG": LogLevels.DEBUG,
            "TRC": LogLevels.TRACE,
            "CRT": LogLevels.CRITICAL,
        }[level]


UnionLogLevel: TypeAlias = Union[LogLevels, LogLevelLiteral]


class LogColor(enum.StrEnum):
    LOG = Fore.WHITE
    INFO = Fore.GREEN
    WARN = Fore.YELLOW
    ERROR = Fore.RED
    DEBUG = Fore.CYAN
    TRACE = Fore.MAGENTA
    CRITICAL = Fore.LIGHTRED_EX


class LogPackage(TypedDict):
    msg: str
    level: LogLevels
    color: str


CallbackFunction = Callable[[LogPackage], Any]


class LogInterface(Protocol):
    callbacks: List[CallbackFunction]

    def log(self, message: str, source: str) -> None: ...

    def info(self, message: str, source: str) -> None: ...

    def warn(self, message: str, source: str) -> None: ...

    def error(self, message: str, source: str) -> None: ...

    def debug(self, message: str, source: str) -> None: ...

    def trace(self, message: str, source: str) -> None: ...

    def critical(self, message: str, source: str) -> None: ...

    def set_callback(self, callback: Function) -> None: ...

    def emit(self, msg: str, source: str, lvl: LogLevels, color: str) -> None:
        for callback in self.callbacks:
            callback(LogPackage(msg=msg, level=lvl, color=color))


class BaseLogger(LogInterface):
    TEMPLATE = "[{time}][{level}][Px{pid}][Tx{thread}]: \n[{source}] {message}"
    LEVELS: Dict[LogLevels, str] = {
        LogLevels.LOG: Fore.WHITE,
        LogLevels.INFO: Fore.GREEN,
        LogLevels.WARN: Fore.YELLOW,
        LogLevels.ERROR: Fore.RED,
        LogLevels.DEBUG: Fore.CYAN,
        LogLevels.TRACE: Fore.MAGENTA,
        LogLevels.CRITICAL: Fore.LIGHTRED_EX,
    }

    def template(self, source: str, lvl: LogLevels, msg: str) -> LogPackage:
        infs = {
            "level": lvl.value,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pid": str(os.getpid()),
            "thread": str(threading.get_ident()),
            "message": msg,
            "source": source,
        }

        return LogPackage(
            msg=self.TEMPLATE.format(**infs),
            level=lvl,
            color=self.LEVELS[lvl],
        )

    def emit(self, msg: str, source: str, lvl: UnionLogLevel, color: str = "") -> None:
        if not isinstance(lvl, LogLevels):
            lvl = LogLevels.from_str(lvl)

        if not color:
            color = self.LEVELS.get(lvl, Fore.WHITE)
        log_package: LogPackage = self.template(source, lvl, msg)
        log_package["color"] = color
        for callback in self.callbacks:
            callback(log_package)

    def set_callback(self, callback: CallbackFunction) -> None:
        self.callbacks.append(callback)

    def log(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.LOG, LogColor.LOG)

    def info(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.INFO, LogColor.INFO)

    def warn(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.WARN, LogColor.WARN)

    def error(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.ERROR, LogColor.ERROR)

    def debug(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.DEBUG, LogColor.DEBUG)

    def trace(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.TRACE, LogColor.TRACE)

    def critical(self, message: str, source: str) -> None:
        self.emit(message, source, LogLevels.CRITICAL, LogColor.CRITICAL)


class NonLogger(BaseLogger):
    callbacks: List[CallbackFunction] = []

    def set_callback(self, callback: Callable[[LogPackage], Any]) -> None:
        pass

    def log(self, message: str, source: str) -> None:
        pass

    def info(self, message: str, source: str) -> None:
        pass

    def warn(self, message: str, source: str) -> None:
        pass

    def error(self, message: str, source: str) -> None:
        pass

    def debug(self, message: str, source: str) -> None:
        pass

    def trace(self, message: str, source: str) -> None:
        pass

    def critical(self, message: str, source: str) -> None:
        pass

    def emit(self, msg: str, source: str, lvl: UnionLogLevel, color: str = "") -> None:
        pass
