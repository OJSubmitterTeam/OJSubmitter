from typing import Any, Callable, Dict, List, Set, Tuple, TypeAlias, Union

Digit: TypeAlias = Union[int, float]
Text: TypeAlias = Union[str, bytes]
Callback: TypeAlias = Callable[..., None]
Function: TypeAlias = Callable[..., Any]
NonArgFunction: TypeAlias = Callable[[], Any]
NonCallback: TypeAlias = Callable[[], None]

BasicType: TypeAlias = Union[
    Digit,
    None,
    str,
    bytes,
    bool,
    List[Any],
    Dict[Any, Any],
    Set[Any],
    Tuple[Any, ...],
]
