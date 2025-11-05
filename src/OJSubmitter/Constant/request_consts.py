from enum import IntEnum
from typing import Dict, Final

LOGGED_TIP = "Please logout First!"


class Language(IntEnum):
    c = 0
    cpp = 1
    pas = 2
    java = 3
    ruby = 4
    bash = 5
    py = 6
    php = 7
    perl = 8
    cs = 9

    @staticmethod
    def from_name(name: str) -> "Language":
        name = name.lower()
        match name:
            case "c":
                return Language.c
            case "cpp":
                return Language.cpp
            case "pas":
                return Language.pas
            case "java":
                return Language.java
            case "ruby":
                return Language.ruby
            case "bash":
                return Language.bash
            case "python" | "py":
                return Language.py
            case "php":
                return Language.php
            case "perl":
                return Language.perl
            case "c#" | "cs":
                return Language.cs
            case _:
                raise ValueError(f"Unsupported language name: {name}")


LANGUAGE_MAP: Final[Dict[str, Language]] = {
    "c": Language.c,
    "cpp": Language.cpp,
    "pas": Language.pas,
    "java": Language.java,
    "ruby": Language.ruby,
    "bash": Language.bash,
    "py": Language.py,
    "php": Language.php,
    "perl": Language.perl,
    "cs": Language.cs,
}
