from typing import Any, Dict, List, Optional, cast


def count_cn_char(s: str) -> int:
    return sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")


def dict_rget_safe(
    d: Any | Dict[Any, Any], key: List[Any], default: Optional[Any] = None
) -> Any:
    if not key:
        return d

    if isinstance(d, dict) and key[0] in d:
        return dict_rget_safe(cast(Any, d[key[0]]), key[1:], default)
    return default
