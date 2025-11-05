from ..Models.resource import ResourceParams
from ..Typehint.remote_cfg import ConfigParams

EMPTY_RESOURCE = ResourceParams(
    local_config={}, cookies={}, history_accounts={}, qt_states={}
)

EMPTY_CONFIG = ConfigParams(base_url="", api_key="", model="")
