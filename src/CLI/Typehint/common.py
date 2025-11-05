from typing import Callable, Dict, TypedDict


class FunctionPackage(TypedDict):
    name: str
    function: Callable[[], None]


FunctionTable = Dict[int, FunctionPackage]
