from typing import Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QComboBox

from ...OJSubmitter.Constant.fields import LAST_LOGIN_ACCOUNT
from ...OJSubmitter.Constant.status import LoginStatus
from ...OJSubmitter.Crawler.crawler import Account
from ...OJSubmitter.Interface.log_interface import BaseLogger
from ...OJSubmitter.Models.identify import AccountParams
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
            FunctionLinker(self.login_account)
            .then(self.update_logged_accounts)
            .then(self.set_current_account)
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

    def __update(self) -> None:
        self.update_account_status()
        self.update_accounts_box()
        self.update_logged_accounts()
        self.switch_to_chosen_account()

    @property
    def history_accounts(self) -> Dict[str, AccountParams]:
        return Resource().resource.history_accounts

    def update_password_text(self) -> None:
        account = self.window.accounts_box.currentText()

        if account in self.history_accounts:
            params = self.history_accounts[account]
            self.window.password_text.setText(params.password)
        else:
            self.window.password_text.clear()

    def update_accounts_box(self) -> None:
        self.window.accounts_box.clear()
        history_accounts = self.history_accounts
        for account, params in history_accounts.items():
            self.window.accounts_box.addItem(account)
            self.window.password_text.setText(params.password)

    def update_remember_checkbox(self) -> None:
        auto_login = self.window.auto_login_checkbox.isChecked()
        if auto_login:  # auto login requires remember password
            self.window.remember_checkbox.setChecked(True)

    def _switch_to_combox_account(self, combox: QComboBox) -> None:
        account = combox.currentText()
        SharedInstances.account_manager.update_current_account(account)

    def set_current_account(self) -> None:
        self._switch_to_combox_account(self.window.accounts_box)

    def switch_to_chosen_account(self) -> None:
        self._switch_to_combox_account(self.window.accounts_to_submit_box)

    def update_logged_accounts(self) -> None:
        self.window.accounts_to_submit_box.clear()
        accounts: List[Account] = []

        for model in self.account_manager.accounts_map.values():
            if model.check_cookie_valid():
                accounts.append(model)

        for cookie in accounts:
            self.window.accounts_to_submit_box.addItem(cookie.account)

    def choose_current_account(self) -> None:
        current = self.account_manager.current_account
        if current is not None:
            index = self.window.accounts_to_submit_box.findText(current.account)
            if index != -1:
                self.window.accounts_to_submit_box.setCurrentIndex(index)

    def accounts_box_switch_to_account(self, account: str) -> None:
        index = self.window.accounts_box.findText(account)
        if index != -1:
            self.window.accounts_box.setCurrentIndex(index)

    def login_account(self) -> None:
        account = self.window.accounts_box.currentText()
        password = self.window.password_text.text()

        acc_obj = Account(account, password)
        lgn_ret = acc_obj.login()
        lgn_status = lgn_ret["status"]

        lole = self.logger.error

        if lgn_status == LoginStatus.ERROR_AUTHENTICATION:
            lole(f"{account}密码错误", source=LogSourceEnum.ACCOUNT_AUTH_SYSTEM)
            return
        if lgn_status == LoginStatus.FAILURE:
            lole(f"{account}登录失败", source=LogSourceEnum.ACCOUNT_AUTH_SYSTEM)
            return
        if lgn_status == LoginStatus.COOKIE_EXPIRED:
            lole(
                f"{account}Cookie过期, 请重新登录",
                source=LogSourceEnum.ACCOUNT_COOKIE_SYSTEM,
            )
            return

        self.logger.emit(
            f"{account}登入成功", source=LogSourceEnum.ACCOUNT_AUTH_SYSTEM, lvl="INF"
        )

        self.account_manager.update_current_account(account=acc_obj)
        self.account_manager.accounts_map[account] = acc_obj

        remember: bool = self.window.remember_checkbox.isChecked()
        if remember:
            self.account_manager.remember_account(account, password)

        auto_login = self.window.auto_login_checkbox.isChecked()
        if auto_login:
            self.account_manager.keep_cookie(account)

        self.update_accounts_box()
        self.accounts_box_switch_to_account(account)

    def logout_account(self) -> None:
        account = self.window.accounts_box.currentText()
        am = SharedInstances.account_manager
        am.logout_account(account)
        self.logger.emit(
            f"{account}已登出", source=LogSourceEnum.ACCOUNT_COOKIE_SYSTEM, lvl="INF"
        )
        self.update_logged_accounts()

    def forget_account(self) -> None:
        account = self.window.accounts_box.currentText()
        self.account_manager.forget_account(account)
        self.logger.emit(
            f"{account}已删除", source=LogSourceEnum.ACCOUNT_AUTH_SYSTEM, lvl="INF"
        )
        self.__update()

    def check_expired_cookies(self) -> None:
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
        r = SharedInstances.resource.resource
        for account in r.cookies.keys():
            if account not in r.history_accounts:
                self.account_manager.logout_account(account)
                continue

    def at_entry(self) -> None:
        # shared instances
        self.account_manager: AccountManager = SharedInstances.account_manager
        self.logger: BaseLogger = SharedInstances.loggers.o_logger

        r = Resource()
        self.account_manager.load_from_resource(r)

        rg = r.local_config_get
        qt_state_restore(
            self.remembered_qwidgets,
            r.resource.qt_states,
        )

        last_account = rg(LAST_LOGIN_ACCOUNT, "")
        self.window.accounts_box.setCurrentText(
            last_account
            if last_account in r.resource.history_accounts
            else self.window.accounts_box.itemText(0)
        )

        self.update_password_text()
        self.check_expired_cookies()
        self.__update()

    def at_exit(self) -> None:
        r = SharedInstances.resource
        store_qt_states(r.resource.qt_states, qt_state_dump(self.remembered_qwidgets))
        r.save()
