from typing import Dict, Optional

from ...OJSubmitter.Constant.defaults import EMPTY_CONFIG
from ...OJSubmitter.Constant.status import LoginStatus
from ...OJSubmitter.Remote.remote_ctl import RemoteController
from ..Crawler.crawler import Account
from ..Interface.log_interface import BaseLogger, NonLogger
from ..Resource import Resource
from ..Typehint.remote_cfg import ConfigParams


class Loggers:
    _initialized: bool = False
    _restored: bool = False

    def __init__(self) -> None:
        if Loggers._initialized:
            raise RuntimeError("Loggers is a singleton class.")
        Loggers._initialized = True

        self._o_logger: BaseLogger = NonLogger()

    @property
    def o_logger(self) -> BaseLogger:
        if not self._initialized:
            raise RuntimeError("Loggers not initialized.")
        if not self._restored:
            raise RuntimeError(
                "Logger not restored. BaseLogger should not be used directly."
            )

        return self._o_logger

    def restore_logger(self, logger: BaseLogger) -> None:
        self._restored = True
        self._o_logger = logger


class AccountManager:
    _initialized: bool = False

    def __init__(self) -> None:
        if AccountManager._initialized:
            raise RuntimeError("AccountManager is a singleton class.")
        AccountManager._initialized = True

        self.accounts_map: Dict[str, Account] = {}
        self.current_account: Optional[Account] = None

    def update_current_account(self, account: Optional[str]) -> None:
        self.current_account = (account and self.accounts_map.get(account)) or None

    def load_from_resource(self, resource: Resource) -> None:
        for acc in resource.resource.history_accounts.values():
            cmodel = resource.resource.cookies.get(acc.account)
            self.accounts_map[acc.account] = Account(
                account=acc.account,
                password=acc.password,
                cookie=cmodel.cookie if cmodel else "",
            )

    def get_password(self, account: str) -> Optional[str]:
        acc = self.accounts_map.get(account)
        if acc:
            return acc.password
        return None

    def login_account(self, account: str, password: Optional[str] = None) -> bool:
        acc: Optional[Account] = self.accounts_map.get(account)
        if acc is None or not acc.check_cookie_valid():
            if password is None:
                return False

            acc = Account(account=account, password=password)
            if acc.login()["status"] != LoginStatus.SUCCESS:
                return False
            self.accounts_map[account] = acc

        return acc.login()["status"] == LoginStatus.SUCCESS

    def remember_account(self, account: str, password: str) -> bool:
        if (
            account in self.accounts_map
            and self.accounts_map[account].password == password
        ):

            return True
        self.accounts_map[account] = Account(account=account, password=password)
        return True

    def logout_account(self, account: str) -> None:
        if account in self.accounts_map:
            del self.accounts_map[account]
        if self.current_account is not None and self.current_account.account == account:
            self.current_account = None

        r: Resource = SharedInstances.resource
        if account in r.resource.cookies:
            del r.resource.cookies[account]
            r.save()

    def forget_account(self, account: str) -> None:
        self.logout_account(account)
        r: Resource = SharedInstances.resource
        if account in r.resource.history_accounts:
            del r.resource.history_accounts[account]
            r.save()

    def clear_accounts(self) -> None:
        self.accounts_map.clear()
        self.current_account = None

        r: Resource = SharedInstances.resource
        r.resource.cookies.clear()
        r.resource.history_accounts.clear()
        r.save()


class Config:
    _initialized: bool = False
    _restored: bool = False

    def __init__(self) -> None:
        if Config._initialized:
            raise RuntimeError("Config is a singleton class.")
        Config._initialized = True
        self._config: ConfigParams = EMPTY_CONFIG

    @property
    def config(self) -> ConfigParams:
        if not self._initialized:
            raise RuntimeError("Config not initialized.")
        if not self._restored:
            raise RuntimeError("Config not restored.")

        return self._config

    def restore_config(self, config: ConfigParams) -> None:
        self._config = config
        self._restored = True


class SharedInstances:
    account_manager: AccountManager = AccountManager()
    loggers: Loggers = Loggers()
    config: Config = Config()
    remote: RemoteController = RemoteController()
    resource: Resource = Resource()
