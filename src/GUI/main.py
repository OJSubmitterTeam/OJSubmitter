import sys
from collections import OrderedDict
from typing import NoReturn

from PyQt6.QtWidgets import QApplication
from qdarkstyle import load_stylesheet_pyqt6  # type: ignore[import-untyped]

from ..OJSubmitter.Store.shared_instances import SharedInstances
from .components.account_logic import AccountLogic
from .components.log_browser_logic import LogBrowserLogic
from .components.problem_logic import LevelModeTableLogic
from .components.settings_logic import SettingsLogic
from .handlers import GUIErrorHandler
from .logger import GUILogger
from .UI import BasicWindow, LogicFrame
from .Util.qt_tools import MsgBtn, qt_dialog


class MainWindow(BasicWindow):
    def __init__(self) -> None:
        super().__init__()
        self.show()

        self.ordered_logics: OrderedDict[str, LogicFrame] = OrderedDict(
            {
                "settings_logic": SettingsLogic(self),
                "log_browser_logic": LogBrowserLogic(self),
                "account_logic": AccountLogic(self),
                "level_table_logic": LevelModeTableLogic(self),
            }
        )

    def at_entry(self) -> None:
        for m in self.ordered_logics.values():
            m.at_entry()

    def at_exit(self) -> None:
        for m in self.ordered_logics.values():
            m.at_exit()


def main() -> NoReturn:
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet_pyqt6())
    window = MainWindow()
    error_handler = GUIErrorHandler(window, openTraceback=True)
    SharedInstances.loggers.restore_logger(GUILogger(window))
    result = error_handler.fetch(
        SharedInstances.remote.check_remote_connection, display_dialog=False
    ).run()
    if isinstance(result, Exception):
        qt_dialog(
            "远程服务连接失败",
            "无法连接到远程服务, 请检查网络连接后重试",
            details=str(result),
            btns=[MsgBtn.OK],
        )
        sys.exit(-1)

    SharedInstances.remote.restore_config_to(SharedInstances.config.restore_config)

    window.at_entry()
    try:
        sys.exit(app.exec())
    finally:
        error_handler.fetch(window.at_exit).run()


if __name__ == "__main__":
    main()
