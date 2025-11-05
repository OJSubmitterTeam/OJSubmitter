from colorama import Fore, Style


def cprint(message: str, color: str = Fore.WHITE) -> None:
    print(f"{color}{message}{Style.RESET_ALL}")
