from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QComboBox

from src.OJSubmitter.Models.identify import AccountParams, CookieModel

from ...OJSubmitter.Crawler.crawler import Account
from ...OJSubmitter.Interface.log_interface import BaseLogger
from ...OJSubmitter.Resource import Resource
from ...OJSubmitter.Store.shared_instances import AccountManager, SharedInstances
from ...Util.function_linker import FunctionLinker
from ..Constant.log_fields import LogSourceEnum
from ..Typehint.qt_items import RecordableQtWidgetSet
from ..UI import BasicWindow, LogicFrame
from ..Util.qt_tools import qt_state_dump, qt_state_restore, store_qt_states


class AccountLogic(LogicFrame):
    def __init__(self, window: BasicWindow) -> None:
        super().__init__(window)

        self.remembered_qwidgets: RecordableQtWidgetSet = {
            self.window.remember_checkbox,
            self.window.accounts_box,
            self.window.auto_login_checkbox,
        }

        self._all_login_logic_fn = (
            FunctionLinker(self.login_account).then(self.update_logged_accounts)
            # .then(self.set_current_account)
            .then(self.choose_current_account)
        )

        self.window.login_btn.clicked.connect(self._all_login_logic_fn)
        self.window.logout_account_btn.clicked.connect(self.logout_account)
        self.window.forget_account_btn.clicked.connect(self.forget_account)

        self.window.accounts_box.currentIndexChanged.connect(self.update_password_text)
        self.window.accounts_to_submit_box.currentIndexChanged.connect(
            self.switch_to_chosen_account
        )
        self.window.auto_login_checkbox.stateChanged.connect(
            self.update_remember_checkbox
        )

        self.window.setKeyPressEventCallback(self._keyPressEvent)

    def _keyPressEvent(self, event: QKeyEvent) -> None:
        match event.key():
            case Qt.Key.Key_Return | Qt.Key.Key_Enter:
                if self.window.accounts_box.hasFocus():
                    self.window.password_text.setFocus()
                elif self.window.password_text.hasFocus():
                    self.login_account()

            case _:
                pass

    def update_password_text(self) -> None:
        """根据accounts_box选择的账号更新密码输入框内容"""
        account = self.window.accounts_box.currentText()

        if account in self.account_manager.accounts_map:
            params = self.account_manager.accounts_map[account]
            self.window.password_text.setText(params.password)
        else:
            self.window.password_text.clear()

    def load_accounts_from_resource(self) -> None:
        """从资源文件加载账号信息到account_manager中"""
        r: Resource = SharedInstances.resource
        self.account_manager.load_from_resource(r)

    def update_accounts_box(self) -> None:
        """刷新accounts_box中的账号列表"""
        self.window.accounts_box.clear()
        accounts = self.account_manager.accounts_map
        for acc in accounts.values():
            self.window.accounts_box.addItem(acc.account)

    def update_remember_checkbox(self) -> None:
        """自动登录需要记住密码，勾选自动登录时强制勾选记住密码"""
        auto_login = self.window.auto_login_checkbox.isChecked()
        if auto_login:  # auto login requires remember password
            self.window.remember_checkbox.setChecked(True)

    def _switch_to_combox_account(self, combox: QComboBox) -> None:
        account = combox.currentText()
        SharedInstances.account_manager.update_current_account(account)

    def switch_to_chosen_account(self) -> None:
        """切换accounts_to_submit_box选择的账号为当前账号"""
        self._switch_to_combox_account(self.window.accounts_to_submit_box)

    def update_logged_accounts(self) -> None:
        """刷新accounts_to_submit_box中的已登录账号列表"""
        self.window.accounts_to_submit_box.clear()
        accounts: List[Account] = []

        for acc in self.account_manager.accounts_map.values():
            if acc.check_cookie_valid():
                accounts.append(acc)

        for acc in accounts:
            self.window.accounts_to_submit_box.addItem(acc.account)

    def _store_account_to_resource(self, account: str, password: str) -> None:
        r: Resource = SharedInstances.resource
        r.resource.history_accounts[account] = AccountParams(
            account=account, password=password
        )
        r.save()

    def _store_cookie_to_resource(self, account: str, cookie: str) -> None:
        r: Resource = SharedInstances.resource
        r.resource.cookies[account] = CookieModel(account=account, cookie=cookie)
        r.save()

    def get_cookie(self, account: str) -> Optional[str]:
        """从account_manager中获取指定账号的cookie"""
        am = SharedInstances.account_manager
        if account in am.accounts_map:
            return am.accounts_map[account].cookie
        return None

    def choose_current_account(self) -> None:
        """切换accounts_to_submit_box到account_manager当前账号"""
        current = self.account_manager.current_account
        if current is not None:
            index = self.window.accounts_to_submit_box.findText(current.account)
            if index != -1:
                self.window.accounts_to_submit_box.setCurrentIndex(index)

    def accounts_box_switch_to_account(self, account: str) -> None:
        """切换accounts_box到指定账号"""
        index = self.window.accounts_box.findText(account)
        if index != -1:
            self.window.accounts_box.setCurrentIndex(index)

    def login_account(self) -> None:
        """登录当前选择的账号"""
        account = self.window.accounts_box.currentText()
        password = self.window.password_text.text()

        lgn_success = self.account_manager.login_account(
            account=account, password=password
        )

        lole = self.logger.error

        if not lgn_success:
            lole(f"{account}登录失败", source=LogSourceEnum.ACCOUNT_AUTH_SYSTEM)
            return

        self.logger.emit(
            f"{account}登入成功", source=LogSourceEnum.ACCOUNT_AUTH_SYSTEM, lvl="INF"
        )

        self.account_manager.update_current_account(account)

        remember: bool = self.window.remember_checkbox.isChecked()
        if remember:
            self.account_manager.remember_account(account, password)
            self._store_account_to_resource(account=account, password=password)

        auto_login = self.window.auto_login_checkbox.isChecked()
        if auto_login:
            ck = self.get_cookie(account=account)
            if ck is None:
                self.logger.emit(
                    f"{account}获取Cookie失败, 无法启用自动登录功能",
                    source=LogSourceEnum.ACCOUNT_COOKIE_SYSTEM,
                    lvl="WRN",
                )
            else:
                self._store_cookie_to_resource(account=account, cookie=ck)

        self.update_accounts_box()
        self.update_logged_accounts()
        self.accounts_box_switch_to_account(account)

    def logout_account(self) -> None:
        """登出当前选择的账号"""
        account = self.window.accounts_box.currentText()
        am = SharedInstances.account_manager
        am.logout_account(account)
        self.logger.emit(
            f"{account}已登出", source=LogSourceEnum.ACCOUNT_COOKIE_SYSTEM, lvl="INF"
        )
        self.update_logged_accounts()

    def forget_account(self) -> None:
        """忘记当前选择的账号"""
        account = self.window.accounts_box.currentText()
        self.account_manager.forget_account(account)
        self.logger.emit(
            f"{account}已删除", source=LogSourceEnum.ACCOUNT_AUTH_SYSTEM, lvl="INF"
        )
        self.update_logged_accounts()
        self.update_accounts_box()

    def check_expired_cookies(self) -> None:
        """检查资源文件中已失效的cookie记录"""
        r = SharedInstances.resource.resource
        for account, cookie_model in r.cookies.items():
            acc = Account(account, cookie=cookie_model.cookie)
            if not acc.check_cookie_valid():
                self.logger.emit(
                    f"{account}的登入状态已失效, 请重新登录",
                    source=LogSourceEnum.ACCOUNT_COOKIE_SYSTEM,
                    lvl="WRN",
                )

    def update_account_status(self) -> None:
        """删除资源文件中无效的cookie记录"""
        r = SharedInstances.resource.resource
        for account in tuple(r.cookies.keys()):
            if account not in r.history_accounts:
                self.account_manager.logout_account(account)

    def at_entry(self) -> None:
        # shared instances
        self.account_manager: AccountManager = SharedInstances.account_manager
        self.logger: BaseLogger = SharedInstances.loggers.o_logger

        r = Resource()
        # load accounts
        self.load_accounts_from_resource()
        self.update_accounts_box()
        self.update_password_text()

        qt_state_restore(
            self.remembered_qwidgets,
            r.resource.qt_states,
        )

        # check cookies
        self.update_account_status()
        self.check_expired_cookies()

        # update logged accounts
        self.update_logged_accounts()

    def at_exit(self) -> None:
        r = SharedInstances.resource
        store_qt_states(r.resource.qt_states, qt_state_dump(self.remembered_qwidgets))
        r.save()
