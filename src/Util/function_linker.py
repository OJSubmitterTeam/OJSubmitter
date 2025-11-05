from typing import Any, List, Self

from ..Typehint.basic import Function


class FunctionLinker:
    def __init__(self, func: Function, *args: Any, **kwargs: Any):
        self.funcs: List[Function] = [func]
        self.args = args
        self.kwargs = kwargs

    def __call__(self) -> Any:
        res: List[Any] = []
        for func in self.funcs:
            res.append(func(*self.args, **self.kwargs))
        return res

    def then(self, func: Function) -> Self:
        self.funcs.append(func)
        return self
