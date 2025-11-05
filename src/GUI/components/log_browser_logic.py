from ...OJSubmitter.Interface.log_interface import LogLevels, LogPackage
from ...OJSubmitter.Store.shared_instances import SharedInstances
from ..UI import BasicWindow, LogicFrame
from ..Util.string_tools import to_html

HtmlColors = {
    LogLevels.LOG: "black",
    LogLevels.INFO: "green",
    LogLevels.WARN: "orange",
    LogLevels.ERROR: "red",
    LogLevels.DEBUG: "yellow",
    LogLevels.TRACE: "purple",
    LogLevels.CRITICAL: "darkred",
}


class LogBrowserLogic(LogicFrame):
    def __init__(self, window: BasicWindow) -> None:
        self.window = window

    def append_log(self, msg_package: LogPackage) -> None:
        html = (
            f"<p style='color: {HtmlColors[msg_package['level']]}'> "
            f"{to_html(msg_package['msg'])}"
            "</p>"
        )

        self.window.log_browser.append(html)
        self.window.log_browser.verticalScrollBar().setValue(
            self.window.log_browser.verticalScrollBar().maximum()
        )

    def at_entry(self) -> None:
        self.logger = SharedInstances.loggers.o_logger

        self.logger.set_callback(callback=self.append_log)

    def at_exit(self) -> None:
        pass
