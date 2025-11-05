from typing import Literal, TypedDict, Union


class BankProblemInfo(TypedDict):
    level_mode: Literal[False]
    id: int


class StageInfo(TypedDict):
    cid: int  # 关卡号


class LevelProblemInfo(TypedDict):
    level_mode: Literal[True]
    topic: str
    cid: int  # 关卡号
    pid: int  # 题号


class OneProblemContent(TypedDict):
    description: str
    input: str
    output: str
    sample_input: str
    sample_output: str
    code_with_filling: str


OneProblemContentLiteral = Literal[
    "description",
    "input",
    "output",
    "sample_input",
    "sample_output",
    "code_with_filling",
]


ProblemModeInfo = Union[BankProblemInfo, LevelProblemInfo]
