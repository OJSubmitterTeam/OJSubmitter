from typing import Any, Dict

from pydantic import BaseModel

from .identify import AccountParams, CookieModel


class ResourceParams(BaseModel):
    qt_states: Dict[str, Any]
    local_config: Dict[str, Any]
    history_accounts: Dict[str, AccountParams]
    cookies: Dict[str, CookieModel]
