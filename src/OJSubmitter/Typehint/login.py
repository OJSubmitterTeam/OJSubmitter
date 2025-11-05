from typing import TypedDict

from ..Constant.status import LoginStatus


class LoginReturn(TypedDict):
    status: LoginStatus
    message: str
