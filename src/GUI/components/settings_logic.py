import sys
import webbrowser

from PyQt6.QtWidgets import QPushButton

from ...GUI.Constant.log_fields import LogSourceEnum
from ...OJSubmitter.Constant.about import TITLE
from ...OJSubmitter.Constant.status import ConfigStatus
from ...OJSubmitter.Resource import Resource
from ...OJSubmitter.Store.shared_instances import SharedInstances
from ...SecretAPI.constant import ABOUT
from ..UI import BasicWindow, LogicFrame
from ..Util.qt_tools import MsgBtn, qt_dialog


class SettingsLogic(LogicFrame):
    def __init__(self, window: BasicWindow):
        super().__init__(window)
        self.reset_all_btn: QPushButton = window.reset_all_btn
        self.reset_all_btn.clicked.connect(self.reset_all)

        self.window.about_btn.clicked.connect(self.about)

    def reset_all(self) -> None:
        choice: MsgBtn = qt_dialog(
            "重置所有设置",
            "这将重置所有设置, 包含账户信息、参数等, 是否继续并重启程序?",
        )

        if choice != MsgBtn.OK:
            return None
        Resource().reset()
        self.logger.info(
            "已重置所有设置, 程序将退出以应用更改",
            source=LogSourceEnum.SETTING_OPERATION_SYSTEM,
        )
        sys.exit(0)

    def check_for_updates(self) -> None:
        cfg = SharedInstances.remote.config
        if cfg["status"] != ConfigStatus.NEED_UPDATE:
            return

        upgrade_info = cfg["data"]
        choice = qt_dialog(
            "有新版本可用",
            (
                f"检测到有新版本可用: {upgrade_info['version']}\n"
                f"下载链接: {upgrade_info['upgrade_url']}\n"
                f"是否前往下载?"
            ),
            btns=[MsgBtn.OK, MsgBtn.CANCEL],
        )
        if choice == MsgBtn.OK:
            webbrowser.open(upgrade_info["upgrade_url"])
        sys.exit(0)

    def about(self) -> None:
        qt_dialog(title=TITLE, msg=ABOUT, btns=None)

    def at_entry(self) -> None:
        self.logger = SharedInstances.loggers.o_logger
        self.check_for_updates()

    def at_exit(self) -> None:
        pass
