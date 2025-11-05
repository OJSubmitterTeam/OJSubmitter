from typing import Literal, NotRequired, TypedDict

from ..Constant.status import ConfigStatus


class ConfigParams(TypedDict):
    base_url: str
    api_key: str
    model: str
    interval: NotRequired[str]


class UpgradeConfigParams(TypedDict):
    """Remote Upgrade Information"""

    upgrade_url: str
    version: str


class ConfigResponseOKParams(TypedDict):
    status: Literal[ConfigStatus.SUCCESS]
    data: ConfigParams


class ConfigResponseUpgradeParams(TypedDict):
    status: Literal[ConfigStatus.NEED_UPDATE]
    data: UpgradeConfigParams


class ConfigResponseFailedParams(TypedDict):
    status: Literal[ConfigStatus.FETCH_FAILED]


ConfigResponseParams = (
    ConfigResponseOKParams | ConfigResponseFailedParams | ConfigResponseUpgradeParams
)
