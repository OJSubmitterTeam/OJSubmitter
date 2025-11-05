import threading
import time
from typing import Dict, List, NoReturn, Optional

from ..OJSubmitter.Constant.request_consts import LANGUAGE_MAP, Language
from ..OJSubmitter.Crawler.crawler import (
    LevelProblemPage,
    ProblemGroup,
    ProblemPackage,
    RunningStatus,
)
from ..OJSubmitter.Remote.remote_ctl import RemoteController
from ..OJSubmitter.Resource import Resource
from ..OJSubmitter.Store.shared_instances import SharedInstances
from ..OJSubmitter.Typehint.problem import LevelProblemInfo, StageInfo
from ..SecretAPI import SecretAPI
from ..Typehint.basic import Digit
from ..Util.functiontools import default_choice, do_nothing
from .Constant.docstring import (
    ACCOUNT_MANAGE_HEADER,
    FUNCTION_TABLE_HEADER,
    MAIN_HEADER,
)
from .Constant.log_fields import LogSourceEnum as LSE
from .logger import logger
from .Typehint.common import FunctionPackage, FunctionTable
from .Util.dynamic_loader import DynamicLoader
from .Util.string_tools import parse_ids


def problem_submit() -> None:
    am = SharedInstances.account_manager
    if am.current_account is None:
        logger.error("请先选择账号", source=LSE.CLI_PROBLEM_SUBMIT)
        return

    # input practice group id
    cid = int(input("请输入练习组ID: ").strip())

    problem_group = ProblemGroup(
        stage=StageInfo(cid=cid),
        account=am.current_account,
    )

    if not problem_group.is_existing:
        logger.error("练习组不存在", source=LSE.CLI_PROBLEM_SUBMIT)
        return

    submit_all_flag = False
    if problem_group.running_status == RunningStatus.NOT_STARTED:
        logger.error("练习组未开始", source=LSE.CLI_PROBLEM_SUBMIT)

        if not default_choice(prompt="是否等待并提交全部未完成题目(Y/n)", default=True):
            return

        submit_all_flag = True
        dynamic_loader = DynamicLoader("等待练习组开始中")
        while problem_group.running_status == RunningStatus.NOT_STARTED:
            dynamic_loader.next_for_times(times=3, interval=1)

    if problem_group.running_status == RunningStatus.END:
        logger.error("练习组已结束", source=LSE.CLI_PROBLEM_SUBMIT)

        if not default_choice(prompt="是否强制提交(y/N)", default=False):
            return

    problem_with_states: List[ProblemPackage] = problem_group.problem_with_states
    idx_to_page: Dict[int, ProblemPackage] = {}
    buffer = "已加载问题列表:\n"
    for idx, problem in enumerate(problem_with_states):
        page: LevelProblemPage = problem["page"]
        finished = problem["finished"]
        info: LevelProblemInfo = page.page_info
        finished_tip = "已完成" if finished else "未完成"

        idx_to_page[idx] = problem
        buffer += (
            f"问题`{idx}`(ID: {info['pid']}, 状态: {finished_tip}): {info['topic']}\n"
        )

    logger.info(buffer, source=LSE.CLI_PROBLEM_SUBMIT)

    # choose problem
    problem_tip = "请输入要提交的题目编号(连续题号用'-'连接, 单个题号用','分隔, 不输入以提交全部): "
    problem_choice = "" if submit_all_flag else input(problem_tip).strip()

    selected_ids: List[int] = (
        [i for i, p in idx_to_page.items() if p["finished"] is False]
        if problem_choice == ""
        else parse_ids(problem_choice)
    )

    pages_to_submit: List[LevelProblemPage] = [
        idx_to_page[i]["page"] for i in selected_ids
    ]
    logger.log(
        f"选择提交题目编号: {selected_ids}",
        source=LSE.CLI_PROBLEM_SUBMIT,
    )

    # choose language
    language_choice = input("请输入提交语言(默认py): ").strip()
    if language_choice and language_choice not in LANGUAGE_MAP:
        logger.error("语言输入错误", source=LSE.CLI_PROBLEM_SUBMIT)
        return

    language: Language = {**LANGUAGE_MAP, "": Language.py}[language_choice]
    remote: RemoteController = SharedInstances.remote

    last_submit_time: Digit = 0

    def submit_once(pts: LevelProblemPage, lang: Language) -> None:
        nonlocal last_submit_time
        ans = None

        def get_ans() -> None:
            nonlocal ans
            ans = remote.get_ai_answer(problem=pts, language=lang)

        thread = threading.Thread(target=get_ans)
        thread.start()

        dl = DynamicLoader("获取答案中")
        while ans is None:
            dl.next_for_times(times=3, interval=0.5)

        if not ans:
            logger.error("未获取到答案, 提交终止", source=LSE.CLI_PROBLEM_SUBMIT)
            return

        logger.debug(f"获取到答案: \n{ans}", source=LSE.CLI_PROBLEM_SUBMIT)
        logger.log(
            f"提交答案到{pts.page_info['topic']}",
            source=LSE.CLI_PROBLEM_SUBMIT,
        )
        pts.submit_code(ans, language_id=lang.value)
        logger.info("答案提交完成", source=LSE.CLI_PROBLEM_SUBMIT)
        last_submit_time = time.time()

    for p in pages_to_submit:
        submit_once(p, language)


def account_manage() -> None:
    # display accounts
    resource: Resource = SharedInstances.resource
    account_manager = SharedInstances.account_manager
    account_manager.load_from_resource(resource)

    acc_map: Dict[int, str] = {}

    def load_accounts() -> None:
        nonlocal acc_map
        acc_map.clear()
        for idx, account in enumerate(account_manager.accounts_map.keys()):
            acc_map[idx] = account

    def show_accounts() -> bool:
        nonlocal acc_map
        if not acc_map:
            logger.warn("当前无已保存账号", source=LSE.CLI_ACCOUNT_MANAGE)
            return False

        buffer = "已加载账号列表:\n"
        for idx, acc in acc_map.items():
            buffer += f"账号`{idx}`: {acc}\n"

        logger.info(buffer, source=LSE.CLI_ACCOUNT_MANAGE)
        return True

    load_accounts()
    while True:
        logger.info(ACCOUNT_MANAGE_HEADER, source=LSE.CLI_ACCOUNT_MANAGE)
        inp = input("请输入操作: ").strip()
        if not inp.isdigit():
            logger.error("操作输入错误, 程序退出", source=LSE.CLI_ACCOUNT_MANAGE)
            return

        match int(inp):
            case 1:  # 切换账号
                has_acc = show_accounts()
                if not has_acc:
                    continue

                choice = input("请输入要使用的账号编号: ").strip()
                if not choice.isdigit() or int(choice) not in acc_map:
                    logger.error("账号编号输入错误", source=LSE.CLI_ACCOUNT_MANAGE)
                    continue

                SharedInstances.account_manager.update_current_account(
                    acc_map[int(choice)]
                )
                logger.info(
                    f"切换到账号: {SharedInstances.account_manager.current_account}",
                    source=LSE.CLI_ACCOUNT_MANAGE,
                )

            case 2:  # 登入账号
                account = input("请输入账号: ").strip()
                password = input("请输入密码: ").strip()
                account_manager.remember_account(account, password)
                account_manager.login_account(account)
                account_manager.keep_cookie(account)
                load_accounts()

            case 3:  # 删除账号
                has_acc = show_accounts()
                if not has_acc:
                    continue

                choice = input("请输入要删除的账号编号: ").strip()
                if not choice.isdigit() or int(choice) not in acc_map:
                    logger.error("账号编号输入错误", source=LSE.CLI_ACCOUNT_MANAGE)
                    continue
                account_manager.forget_account(acc_map[int(choice)])
                load_accounts()

            case 4:  # 显示账号列表
                show_accounts()

            case 5:  # 返回
                return

            case _:
                logger.error("操作编号输入错误", source=LSE.CLI_ACCOUNT_MANAGE)
                continue


def choose_function(functions: FunctionTable) -> int:
    tip = FUNCTION_TABLE_HEADER

    for index, f in sorted(functions.items(), key=lambda x: x[0]):
        tip += f"{index}, {f['name']}\n"

    logger.info(tip, source=LSE.CLI_CHOOSE_FUNCTION)

    choice = input("请输入功能编号: ").strip()
    if not choice.isdigit() or int(choice) not in functions:
        logger.error("功能编号输入错误, 程序退出", source=LSE.CLI_CHOOSE_FUNCTION)
        return -1
    functions[int(choice)]["function"]()
    return int(choice)


def network_check() -> Optional[NoReturn]:
    try:
        SharedInstances.remote.check_remote_connection()
        return None
    except Exception as e:
        logger.critical("远程连接异常, 程序终止", source=LSE.CLI_NETWORK_CHECK)
        input("请按回车键退出...")
        raise SystemExit from e


def main() -> None:
    network_check()

    SharedInstances.remote.restore_config_to(SharedInstances.config.restore_config)
    logger.log(MAIN_HEADER.format(VERSION=SecretAPI.__VERSION__), source=LSE.CLI_MAIN)
    function_map: FunctionTable = {
        1: FunctionPackage(name="账号管理", function=account_manage),
        2: FunctionPackage(name="问题提交", function=problem_submit),
        9: FunctionPackage(name="退出", function=do_nothing),
    }

    while True:
        current_account = SharedInstances.account_manager.current_account
        current_acc = current_account and current_account.account
        (logger.info if current_acc else logger.warn)(
            f"当前选择账号: {current_acc or '未选择'}",
            source=LSE.CLI_MAIN,
        )
        choice = choose_function(function_map)
        if choice == -1:
            logger.error("功能选择错误, 程序退出", source=LSE.CLI_MAIN)
            break

        if choice == 9:  # Exit
            logger.info("程序结束", source=LSE.CLI_MAIN)
            break


if __name__ == "__main__":
    main()
