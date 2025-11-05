from pydantic import BaseModel


class AccountParams(BaseModel):
    account: str
    password: str


class CookieModel(BaseModel):
    account: str
    cookie: str
