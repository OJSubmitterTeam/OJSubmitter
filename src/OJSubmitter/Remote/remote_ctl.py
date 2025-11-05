from functools import cached_property
from typing import Callable, NoReturn, Optional

import requests

from ...OJSubmitter.Constant.request_consts import Language
from ...OJSubmitter.Constant.status import ConfigStatus
from ...OJSubmitter.Crawler.crawler import LevelProblemPage
from ...SecretAPI import SecretAPI
from ...SecretAPI.remote import PermissionResponseParams, PermissionStatus, get_config
from ...Util.common import dict_rget_safe
from ..Typehint.remote_cfg import ConfigParams, ConfigResponseParams

CONFIG_NAME = SecretAPI.CONFIG_NAME
GET_CONFIG_URL = SecretAPI.GET_CONFIG_URL
GET_SOFTWARE_PERMISSION_URL = SecretAPI.GET_SOFTWARE_PERMISSION_URL
GET_CALLBACK_URL = SecretAPI.GET_CALLBACK_URL
USE_SOFTWARE_PERMISSION_URL = SecretAPI.USE_SOFTWARE_PERMISSION_URL

from ...SecretAPI.remote import get_ai_answer, is_permitted, use_permission


class RemoteController:
    def __init__(self) -> None:
        pass

    @cached_property
    def config(self) -> ConfigResponseParams:
        return get_config()

    def use_permission(self, account: str) -> PermissionResponseParams:
        return use_permission(account)

    def is_permitted(self, account: str) -> PermissionStatus:
        return is_permitted(account)

    def get_ai_answer(
        self,
        problem: LevelProblemPage,
        language: Language,
        timeout: float = 60,
    ) -> str:
        return get_ai_answer(problem, language, timeout)

    def check_remote_connection(self) -> Optional[NoReturn]:
        resp = requests.post(GET_CONFIG_URL, timeout=5)
        resp.raise_for_status()
        return None

    def restore_config_to(self, callback: Callable[[ConfigParams], None]) -> None:
        cfg = self.config
        if cfg["status"] == ConfigStatus.SUCCESS:
            callback(cfg["data"])

    def raise_upgrade_status(self) -> None:
        if self.config["status"] == ConfigStatus.NEED_UPDATE:
            raise RuntimeError("A new version of OJSubmitter is available.")

    def __repr__(self) -> str:
        return (
            f"<RemoteController "
            f"status={self.config['status'].name} "
            f"remote_version={dict_rget_safe(self.config, ['data', 'version'], 'N/A')}>"
        )
