import enum


class LoginStatus(enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR_AUTHENTICATION = "error_authentication"
    COOKIE_EXPIRED = "cookie_expired"


class ConfigStatus(enum.Enum):
    SUCCESS = 0
    FETCH_FAILED = 1
    NEED_UPDATE = 2
