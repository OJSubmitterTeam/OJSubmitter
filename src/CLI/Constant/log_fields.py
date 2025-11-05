from enum import StrEnum


class LogSourceEnum(StrEnum):
    CLI_MAIN = "CLI.main"
    CLI_CHOOSE_FUNCTION = "CLI.choose_function"
    CLI_ACCOUNT_MANAGE = "CLI.account_manage"
    CLI_PROBLEM_SUBMIT = "CLI.problem_submit"
    CLI_NETWORK_CHECK = "CLI.network_check"
