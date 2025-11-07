import hashlib
import re
import threading
import time
from enum import StrEnum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict, cast

import requests
from bs4 import BeautifulSoup, ResultSet, Tag

from ...OJSubmitter.Models.identify import CookieModel
from ...Typehint.basic import Callback, NonCallback
from ...Util.functiontools import do_nothing
from ..Constant.request_consts import LOGGED_TIP, Language
from ..Constant.status import LoginStatus
from ..Resource import Resource
from ..Typehint.login import LoginReturn
from ..Typehint.problem import (
    LevelProblemInfo,
    OneProblemContent,
    OneProblemContentLiteral,
    StageInfo,
)


class Account:
    def __init__(self, account: str, password: str = "", cookie: str = "") -> None:
        self.account = account
        self.password = password
        self._cookie = cookie

    def _check_is_login(self, new_cookie: Optional[str] = None) -> bool:
        url = "http://10.88.108.125/loginpage.php"
        response = requests.get(
            url,
            cookies={"PHPSESSID": self._cookie if new_cookie is None else new_cookie},
        )
        response.encoding = "utf-8"
        return LOGGED_TIP in response.text

    @property
    def is_logined(self) -> bool:
        if not self._cookie:
            return False
        return self._check_is_login()

    def set_cookie(self, cookie: str) -> None:
        if self._check_is_login(cookie):
            self._cookie = cookie
        return

    def _get_phpsessid(self) -> str:
        session: requests.Session = requests.Session()
        hashed_password: str = hashlib.md5(self.password.encode()).hexdigest()

        response = session.post(
            url="http://10.88.108.125/login.php",
            data={
                "user_id": self.account,
                "password": hashed_password,
                "submit": "Submit",
            },
        )
        response.raise_for_status()

        phpsessid: str = str(session.cookies.get("PHPSESSID"))
        return phpsessid

    def login(self) -> LoginReturn:
        try:
            if self.is_logined:
                return LoginReturn(
                    status=LoginStatus.SUCCESS, message="Already logged in."
                )

            if not self.password:
                return LoginReturn(
                    status=LoginStatus.ERROR_AUTHENTICATION,
                    message="Password is empty. Cannot log in.",
                )

            self._cookie = self._get_phpsessid()
            if not self._cookie:
                return LoginReturn(
                    status=LoginStatus.FAILURE,
                    message="Failed to retrieve session.",
                )

        except Exception as e:
            return LoginReturn(
                status=LoginStatus.FAILURE,
                message=f"An error occurred during login: {e}",
            )

        if not self.is_logined:
            return LoginReturn(
                status=LoginStatus.ERROR_AUTHENTICATION,
                message="Authentication failed. Please check your credentials.",
            )

        return LoginReturn(status=LoginStatus.SUCCESS, message="Logging successful.")

    def check_cookie_valid(self) -> bool:
        return self._check_is_login()

    @property
    def is_cookie_valid(self) -> bool:
        return self._check_is_login()

    @property
    def cookie(self) -> str:
        resource = Resource()
        cookie_model = resource.resource.cookies.get(self.account)
        if not cookie_model:
            return self._cookie
        account, cookie = cookie_model.account, cookie_model.cookie
        if cookie and account == self.account and self._check_is_login(cookie):
            resource.resource.cookies[account] = CookieModel(
                account=account, cookie=cookie
            )
            resource.save()

            return cookie

        return self._cookie

    def __repr__(self) -> str:
        return f"Account(account={self.account}, password=****, cookie={self._cookie})"


class LevelProblemPage:
    def __init__(self, page_info: LevelProblemInfo, account: Account) -> None:
        self.page_info = page_info
        self.account = account
        self.reload_page()

    def reload_page(self) -> None:
        self.page_text: str = self.get_page()
        self.page_content: OneProblemContent = self.parse_page()

    def get_page(self) -> str:
        url = f"http://10.88.108.125/sproblem.php?cid={self.page_info['cid']}&pid={self.page_info['pid']}"
        response = requests.get(url, cookies={"PHPSESSID": self.account.cookie})
        response.encoding = "utf-8"
        if response.status_code == 200:
            return response.text
        return ""

    @property
    def is_problem_running(self) -> bool:
        page = self.get_page()
        if "该关卡尚未开始" in page or "请耐心等候" in page:
            return False
        self.reload_page()
        return True

    def parse_page(self) -> OneProblemContent:
        soup = BeautifulSoup(self.page_text, "html.parser")
        returns: OneProblemContent = OneProblemContent(
            description="",
            input="",
            output="",
            sample_input="",
            sample_output="",
            code_with_filling="",
        )

        def get_section_by_h2(title: str) -> str:
            h2: Optional[Tag] = soup.find("h2", string=cast(Any, title))
            if not h2:
                return ""
            content_div = h2.find_next_sibling("div", class_="content")
            if not content_div:
                return ""
            sample_span = content_div.find("span", class_="sampledata")
            if sample_span:
                return sample_span.get_text(strip=True)
            pre = content_div.find("pre")
            if pre:
                return pre.get_text()
            return content_div.get_text(strip=True)

        mp = {
            "题目描述": "description",
            "输入": "input",
            "输出": "output",
            "样例输入": "sample_input",
            "样例输出": "sample_output",
            "带填充标签的C/C++原程序": "code_with_filling",
        }

        for cn, en in mp.items():
            returns[cast(OneProblemContentLiteral, en)] = get_section_by_h2(cn)

        return returns

    def parse_running_id(self, status_page: str) -> Optional[int]:
        soup = BeautifulSoup(status_page, "html.parser")
        result_table = soup.find("table", id="result-tab")
        if not result_table:
            return None
        instances = result_table.find_all("tr", class_=re.compile("^(evenrow|oddrow)$"))
        if not instances:
            return None
        first_instance = instances[0]
        tds = first_instance.find_all("td")
        if len(tds) < 1:
            return None
        running_id_str: str = tds[0].get_text(strip=True)
        if not running_id_str.isdigit():
            return None
        return int(running_id_str)

    def get_full_content(self, language: Language) -> str:
        if not self.page_content.get("description"):
            return ""

        full_content = ""
        for k, v in self.page_content.items():
            full_content += f"{k:-^30}\n{v}\n\n"
        lan = f"要求语言:{language.name}"
        full_content += f"{lan:-^30}\n"
        return full_content

    def submit_code(
        self,
        code: str,
        language_id: int,
        fetch_running_id: bool = False,
    ) -> Optional[int]:
        code = re.sub(r'(?<![\'"])\n', "\r\n", code)
        form: Dict[str, str | int] = {
            "cid": self.page_info["cid"],
            "pid": self.page_info["pid"],
            "language": language_id,
            "source": code,
        }

        headers: Dict[str, str] = {}

        cookies: Dict[str, str] = {
            "PHPSESSID": f"{self.account.cookie}",
        }

        resp: requests.Response = requests.post(
            url="http://10.88.108.125/ssubmit.php",
            data=form,
            headers=headers,
            cookies=cookies,
        )
        resp.encoding = "utf-8"
        resp.raise_for_status()

        if fetch_running_id:
            page = resp.text
            return self.parse_running_id(page)

        return None

    def __repr__(self) -> str:
        return f"LevelProblemPage(page_info={self.page_info}, cookie={self.account.cookie})"


class ProblemPackage(TypedDict):
    page: LevelProblemPage
    finished: bool


class RunningStatus(StrEnum):
    NOT_STARTED = "未开始"
    RUNNING = "运行中"
    ENDED = "已结束"
    NO_ACCESS = "关卡被屏蔽或者无权进入"


class ProblemGroup:
    def __init__(self, stage: StageInfo, account: Account) -> None:
        self.stage: StageInfo = stage
        self.account: Account = account

    @property
    def problems(self) -> List[LevelProblemPage]:
        pws = self.problem_with_states

        return [ppack["page"] for ppack in pws]

    @property
    def problem_with_states(self) -> List[ProblemPackage]:
        url = f"http://10.88.108.125/stage.php?cid={self.stage['cid']}"
        resp = requests.get(url, cookies={"PHPSESSID": self.account.cookie})
        resp.encoding = "utf-8"
        if resp.status_code == 200:
            soup: BeautifulSoup = BeautifulSoup(resp.text, "html.parser")
            problem_rows: List[Tag] = soup.select("#problemset tbody tr")
            problems: List[ProblemPackage] = []
            for index, row in enumerate(problem_rows):
                tds = row.find_all("td")
                if len(tds) < 1:
                    continue

                lpi = LevelProblemInfo(
                    level_mode=True,
                    cid=self.stage["cid"],
                    pid=index,
                    topic=tds[2].get_text(strip=True),
                )
                ppage = LevelProblemPage(
                    page_info=lpi,
                    account=self.account,
                )

                ppack = ProblemPackage(
                    page=ppage,
                    finished=tds[0].get_text(strip=True) == "Y",
                )
                problems.append(ppack)
            return problems
        return []

    @property
    def running_status(self) -> RunningStatus:
        url = f"http://10.88.108.125/stage.php?cid={self.stage['cid']}"
        resp = requests.get(url, cookies={"PHPSESSID": self.account.cookie})
        resp.encoding = "utf-8"

        if RunningStatus.NO_ACCESS in resp.text:
            return RunningStatus.NO_ACCESS

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            center_divs: ResultSet[Tag] = soup.select("#main center")
            for center in center_divs:
                status_spans = center.find_all("span")
                for span in status_spans:
                    span_text = span.get_text(strip=True)
                    if RunningStatus.RUNNING in span_text:
                        return RunningStatus.RUNNING
                    elif RunningStatus.ENDED in span_text:
                        return RunningStatus.ENDED

        return RunningStatus.NOT_STARTED

    @property
    def is_running(self) -> bool:
        status = self.running_status
        return status == RunningStatus.RUNNING

    @property
    def is_existing(self) -> bool:
        url = f"http://10.88.108.125/stage.php?cid={self.stage['cid']}"
        resp = requests.get(url, cookies={"PHPSESSID": self.account.cookie})
        resp.encoding = "utf-8"
        if "没有这样的关卡!" in resp.text:
            return False
        return True

    def wait_for_start(
        self,
        next_fn: Optional[Callback] = None,
        callback: Optional[Callable[..., Any]] = None,
        interval: float = 3.0,
    ) -> Optional[Tuple[NonCallback, Optional[int]]]:
        """等待关卡开始运行


        NOTE: 如果callback为None, 则为同步调用. 否则为其创建一个线程(stl thread).
        Args:
            next_fn (Optional[Callback], optional): 每次轮询前调用的函数. Defaults to None.
            callback (Optional[Callable[..., Any]], optional): 关卡开始后调用的函数. Defaults to None.
            interval (float, optional): 轮询间隔. Defaults to 3.0. sec

        Returns:
            Optional[Tuple[NonCallback, Optional[int]]]: 如果没有callback 则返回停止函数和线程ID. 否则返回None.
        """
        next_fn = next_fn or do_nothing

        run = True

        def loop() -> None:
            while run:
                if self.is_running:
                    break
                next_fn()
                time.sleep(interval)
            if callback is not None:
                callback()

        def stop() -> None:
            nonlocal run
            run = False

        if callback is None:
            loop()
            return None

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return stop, t.ident
