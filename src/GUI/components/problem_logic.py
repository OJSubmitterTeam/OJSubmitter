import time
from enum import IntEnum
from typing import List, Optional, Tuple, TypedDict

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QTableWidgetItem

from ...OJSubmitter.Constant.request_consts import Language
from ...OJSubmitter.Crawler.crawler import (
    LevelProblemPage,
    ProblemGroup,
    ProblemPackage,
    RunningStatus,
)
from ...OJSubmitter.Interface.log_interface import BaseLogger, LogLevels
from ...OJSubmitter.Store.shared_instances import AccountManager, SharedInstances
from ...OJSubmitter.Typehint.problem import LevelProblemInfo
from ...OJSubmitter.Typehint.remote_cfg import ConfigParams
from ...Typehint.basic import Digit, NonCallback
from ...Util.function_linker import FunctionLinker
from ...Util.functiontools import closure
from ..Constant.log_fields import LogSourceEnum
from ..Typehint.qt_items import RecordableQtWidgetSet
from ..UI import BasicWindow, LogicFrame
from ..Util.qt_tools import qt_state_dump, qt_state_restore, store_qt_states


class QThreadSignalInfo(IntEnum):
    run_finished = 1
    works_finished = 2


class RespondentThread(QThread):
    signal_info = pyqtSignal(int)  # QThreadSignalInfo
    process_msg = pyqtSignal(str, str)  # str, LogLevels

    @staticmethod
    def load_from_group(
        parent: Optional[QObject],
        problem_group: ProblemGroup,
        language: Language,
        callback: Optional[NonCallback] = None,
        submit_directly: bool = False,
    ) -> "RespondentThread":
        return RespondentThread(
            group=problem_group,
            language=language,
            parent=parent,
            callback=callback,
            submit_directly=submit_directly,
        )

    @staticmethod
    def load_from_problems(
        parent: Optional[QObject],
        problems: List[LevelProblemPage],
        language: Language,
        callback: Optional[NonCallback] = None,
        submit_directly: bool = False,
    ) -> "RespondentThread":
        return RespondentThread(
            problems=problems,
            language=language,
            parent=parent,
            callback=callback,
            submit_directly=submit_directly,
        )

    def __init__(
        self,
        parent: Optional[QObject] = None,
        *,
        problems: Optional[List[LevelProblemPage]] = None,
        group: Optional[ProblemGroup] = None,
        language: Language,
        callback: Optional[NonCallback] = None,
        submit_directly: bool = False,
    ) -> None:
        super().__init__(parent)

        # shared instances
        self.account_manager: AccountManager = SharedInstances.account_manager
        self.logger: BaseLogger = SharedInstances.loggers.o_logger
        self.config: ConfigParams = SharedInstances.config.config

        self.problems: List[LevelProblemPage] = problems or []
        self.group: Optional[ProblemGroup] = group
        self.language: Language = language
        self.callback = callback
        self.submit_directly = submit_directly
        self._terminate = False
        self._interval: Digit = 10  # default 10 secs

    def set_interval(self, seconds: float) -> None:
        self._interval = seconds

    def wait_for_start(
        self,
        next_fn: Optional[NonCallback] = None,
    ) -> None:
        if self.group is None:
            return None

        while True:
            if self._terminate:
                return None

            if not self.group.is_running or any(
                p.is_problem_running for p in self.problems
            ):
                if next_fn:
                    next_fn()

                time.sleep(1.5)
                continue
            break

    def run(self) -> None:
        if not self.submit_directly:
            self.wait_for_start(self.callback)
        if self._terminate:
            self.signal_info.emit(QThreadSignalInfo.run_finished)
            return None

        problems = self.problems
        if self.group is not None:
            problems = self.group.problems

        last_sub_time: Digit = 0

        for p in problems:
            tpc = p.page_info["topic"]
            self.process_msg.emit(f"正在提交`{tpc}`", LogLevels.WARN)

            rmt = SharedInstances.remote
            up = rmt.use_permission(p.account.account)

            self.process_msg.emit(
                f"`{p.account.account}`剩余余额:{up['quota']}token(s)", LogLevels.INFO
            )

            ans = rmt.get_ai_answer(
                problem=p,
                language=self.language,
            )

            self.process_msg.emit(f"`{tpc}` 获取答案完成: \n{ans}", LogLevels.INFO)

            need_wait = last_sub_time + self._interval - time.time()
            if need_wait > 0:
                self.process_msg.emit(f"等待 {need_wait:.2f} 秒", LogLevels.DEBUG)
                time.sleep(need_wait)

            if not ans:
                continue

            p.submit_code(ans, self.language)
            last_sub_time = time.time()
            self.process_msg.emit(f"提交`{tpc}`完成", LogLevels.INFO)

        self.signal_info.emit(
            QThreadSignalInfo.run_finished | QThreadSignalInfo.works_finished
        )

    def terminate(self) -> None:
        self._terminate = True

    @property
    def is_alive(self) -> bool:
        return not self._terminate and self.isRunning()


class LevelModeTableLogic(LogicFrame):
    def __init__(self, window: BasicWindow):
        super().__init__(window)

        # remembered widgets
        self.remembered_qwidgets: RecordableQtWidgetSet = {
            self.window.auto_detect_checkbox,
            self.window.cid_text,
            self.window.language_combox,
            self.window.force_submit_checkbox,
            self.window.submit_interval_spin,
        }

        self.init_instances()
        self.update_frames()

        def uf_fn(x: NonCallback) -> NonCallback:
            return FunctionLinker(x).then(self.update_frames)

        # table opr
        ## btns
        self.window.detect_problem_btn.clicked.connect(uf_fn(self.detect_problems))
        self.window.choose_all_btn.clicked.connect(uf_fn(self.switch_all))
        self.window.reverse_btn.clicked.connect(uf_fn(self.reverse_selection))
        self.window.auto_choose_btn.clicked.connect(uf_fn(self.auto_choose_problems))
        ## checkboxs
        self.window.auto_detect_checkbox.stateChanged.connect(self.update_auto_detect)

        # problem opr
        ## btns
        self.window.submit_btn.clicked.connect(self.submit_problems)
        self.window.auto_wait_submit_btn.clicked.connect(self.auto_wait_submit)
        self.window.cancel_submit_btn.clicked.connect(self.stop_submit)

        # flags
        self._timeout_connected = False

    def init_instances(self) -> None:
        self.debounce = QTimer()
        self.debounce.setSingleShot(True)

        self.problem_group: Optional[ProblemGroup] = None
        self.respondent_threads: List[RespondentThread] = []

    def update_frames(self) -> None:
        self.update_choose_all_btn_text()

    def update_auto_detect(self) -> None:
        """[勾选框.行为]自动检测逻辑更新"""
        to_auto_detect = self.window.auto_detect_checkbox.isChecked()
        if to_auto_detect:
            self.detect_problems()

        # prevent multiple disconnect
        if not to_auto_detect and not self._timeout_connected:
            return None

        # init debounce timer
        timeout = self.debounce.timeout
        (timeout.connect if to_auto_detect else timeout.disconnect)(
            self.detect_problems
        )

        if not self._timeout_connected:
            self._closured_debounce_start = closure(self.debounce.start, 300)

        # account box change
        signal = self.window.accounts_to_submit_box.currentIndexChanged
        (signal.connect if to_auto_detect else signal.disconnect)(
            self._closured_debounce_start
        )

        # cid text change
        signal = self.window.cid_text.textChanged
        (signal.connect if to_auto_detect else signal.disconnect)(
            self._closured_debounce_start
        )

        self._timeout_connected = to_auto_detect

    def reverse_selection(self) -> None:
        """[按钮.行为]反选所有题目"""
        for row in range(self.window.problem_table.rowCount()):
            widget = self.window.problem_table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(not widget.isChecked())

    def is_table_empty(self) -> bool:
        return self.window.problem_table.rowCount() == 0

    def is_table_all_checked(self) -> Optional[bool]:
        """是否全部选中, 空表返回None"""
        if self.is_table_empty():
            return None
        for row in range(self.window.problem_table.rowCount()):
            widget = self.window.problem_table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                if not widget.isChecked():
                    return False
        return True

    def update_choose_all_btn_text(self) -> None:
        """[按钮.文字]更新[全选/全不选]按钮"""
        all_checked = self.is_table_all_checked()
        if all_checked is None:
            self.window.choose_all_btn.setText("全选/全不选")
            return None
        self.window.choose_all_btn.setText("全不选" if all_checked else "全选")

    def switch_all(self) -> None:
        """[按钮.行为]切换[全选/全不选]状态"""
        all_checked = self.is_table_all_checked()
        if all_checked is None:
            return None

        for row in range(self.window.problem_table.rowCount()):
            widget = self.window.problem_table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(not all_checked)

    def auto_choose_problems(self) -> None:
        """[按钮.行为]自动选择未完成题目"""
        if self.is_table_empty():
            return None

        for row in range(self.window.problem_table.rowCount()):
            checkbox = self.window.problem_table.cellWidget(row, 0)
            item = self.window.problem_table.item(row, 1)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(item.text() != "Finished")

    def create_table_line(
        self,
        finished: bool,
        problem_id: str,
        problem_topic: str,
    ) -> Tuple[QCheckBox, QTableWidgetItem, QTableWidgetItem, QTableWidgetItem]:
        """创建题目表格行组件"""
        select = not finished
        checkbox = QCheckBox(self.window.problem_table)
        checkbox.setChecked(select)
        checkbox.stateChanged.connect(self.update_choose_all_btn_text)
        finished_item = QTableWidgetItem("Finished" if finished else "Unfinished")
        id_item = QTableWidgetItem(problem_id)
        topic_item = QTableWidgetItem(problem_topic)

        return (
            checkbox,
            finished_item,
            id_item,
            topic_item,
        )

    def clear_table(self) -> None:
        """清空题目表格"""
        self.window.problem_table.setRowCount(0)

    def detect_problems(self) -> None:
        """[按钮.行为]检测题目, 更新列表与状态"""
        self.problem_group = None
        cid_txt = self.window.cid_text.text().strip()
        if cid_txt == "":
            self.clear_table()
            return None
        if cid_txt.isnumeric() is False:
            self.logger.emit(
                f"请输入有效的关卡ID",
                source=LogSourceEnum.PROBLEM_DETECT_SYSTEM,
                lvl="WRN",
            )
            return None

        cid = int(cid_txt)
        if self.account_manager.current_account is None:
            self.logger.error(
                "当前没有登录的账号",
                source=LogSourceEnum.PROBLEM_DETECT_SYSTEM,
            )
            return None

        self.problem_group = ProblemGroup(
            {"cid": cid}, self.account_manager.current_account
        )

        if not self.problem_group.is_existing:
            self.clear_table()
            self.logger.emit(
                f"{cid} 关卡不存在",
                source=LogSourceEnum.PROBLEM_DETECT_SYSTEM,
                lvl="ERR",
            )
            self.window.problem_status_label.setText("不存在")
            return None

        status: RunningStatus = self.problem_group.running_status

        if status == RunningStatus.NOT_STARTED:
            self.logger.emit(
                f"{cid} 关卡未开启",
                source=LogSourceEnum.PROBLEM_DETECT_SYSTEM,
                lvl="WRN",
            )
            self.clear_table()
            self.window.problem_status_label.setText("未开启")
            return None
        elif status == RunningStatus.ENDED:
            self.logger.emit(
                f"{cid} 关卡已结束",
                source=LogSourceEnum.PROBLEM_DETECT_SYSTEM,
                lvl="WRN",
            )
            self.window.problem_status_label.setText("已结束")
        elif status == RunningStatus.NO_ACCESS:
            self.logger.emit(
                f"{cid} 关卡无权限访问",
                source=LogSourceEnum.PROBLEM_DETECT_SYSTEM,
                lvl="ERR",
            )
            self.clear_table()
            self.window.problem_status_label.setText("无权限")
            return None
        else:
            self.window.problem_status_label.setText("运行中")

        problems: List[ProblemPackage] = self.problem_group.problem_with_states
        self.window.problem_table.setRowCount(len(problems))
        for i, problem in enumerate(problems):
            page: LevelProblemPage = problem["page"]
            page_info = page.page_info
            button, finished_item, id_item, topic_item = self.create_table_line(
                problem["finished"],
                str(page_info["pid"]),
                page_info["topic"],
            )
            self.window.problem_table.setCellWidget(i, 0, button)
            self.window.problem_table.setItem(i, 1, finished_item)
            self.window.problem_table.setItem(i, 2, id_item)
            self.window.problem_table.setItem(i, 3, topic_item)

        self.update_frames()

    def get_selected_problems(self) -> Optional[List[LevelProblemPage]]:
        """[按钮.行为]提交选中题目"""

        Pack = TypedDict("Pack", {"pid": int, "topic": str, "problem_id": str})

        packs: List[Pack] = []
        for row_also_pid in range(self.window.problem_table.rowCount()):
            checkbox = self.window.problem_table.cellWidget(row_also_pid, 0)
            topic_item = self.window.problem_table.item(row_also_pid, 3)
            id_item = self.window.problem_table.item(row_also_pid, 2)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                packs.append(
                    Pack(
                        pid=int(id_item.text()) if id_item else -1,
                        topic=topic_item.text() if topic_item else "未知",
                        problem_id=id_item.text() if id_item else "",
                    )
                )

        if not packs:
            self.logger.warn(
                "未选中任何题目", source=LogSourceEnum.PROBLEM_SELECTION_SYSTEM
            )
            return None

        if self.account_manager.current_account is None:
            self.logger.error(
                "当前没有登录的账号", source=LogSourceEnum.PROBLEM_SELECTION_SYSTEM
            )
            return None

        if self.problem_group is None:
            self.logger.error(
                "未检测到题目列表", source=LogSourceEnum.PROBLEM_SELECTION_SYSTEM
            )
            return None

        return [
            LevelProblemPage(
                page_info=LevelProblemInfo(
                    level_mode=True,
                    cid=self.problem_group.stage["cid"],
                    pid=pack["pid"],
                    topic=pack["topic"],
                ),
                account=self.account_manager.current_account,
            )
            for pack in packs
        ]

    def submit_problems(self) -> None:
        if self.problem_group is None:
            self.logger.error(
                "未检测到题目列表", source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM
            )
            return None

        force_submit = self.window.force_submit_checkbox.isChecked()
        if not self.problem_group.is_running and not force_submit:
            self.logger.error("题组未开启", source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM)
            return None

        problems = self.get_selected_problems()
        if problems is None:
            return None

        wk = RespondentThread.load_from_problems(
            parent=self.window,
            problems=problems,
            language=Language.from_name(self.window.language_combox.currentText()),
            submit_directly=force_submit,
        )
        self.respondent_threads.append(wk)

        def ret(info: QThreadSignalInfo) -> None:
            is_works_finished = QThreadSignalInfo.works_finished & info
            is_run_finished = QThreadSignalInfo.run_finished & info
            if is_works_finished:
                self.logger.emit(
                    "提交完成",
                    source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM,
                    lvl="TRC",
                )
            if is_run_finished and wk in self.respondent_threads:
                self.respondent_threads.remove(wk)

        def wk_logger(msg: str, lvl: LogLevels) -> None:
            self.logger.emit(
                msg,
                source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM,
                lvl=lvl,
            )

        wk.signal_info.connect(ret)
        wk.process_msg.connect(wk_logger)
        wk.start()

    def auto_wait_submit(self) -> None:
        cid = self.window.cid_text.text().strip()
        if cid == "" or cid.isnumeric() is False:
            self.logger.warn(
                "请输入有效的关卡ID", source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM
            )
            return None

        if self.account_manager.current_account is None:
            self.logger.error(
                "当前没有登录的账号", source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM
            )
            return None

        self.problem_group = ProblemGroup(
            {"cid": int(cid)}, self.account_manager.current_account
        )

        wk = RespondentThread.load_from_group(
            parent=self.window,
            problem_group=self.problem_group,
            callback=lambda: self.logger.emit(
                "自动提交等待中...",
                source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM,
                lvl="INF",
            ),
            language=Language.from_name(self.window.language_combox.currentText()),
        )
        self.respondent_threads.append(wk)

        def ret(info: QThreadSignalInfo) -> None:
            is_works_finished = QThreadSignalInfo.works_finished & info
            is_run_finished = QThreadSignalInfo.run_finished & info
            if is_works_finished:
                self.logger.emit(
                    "提交完成",
                    source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM,
                    lvl="TRC",
                )
            if is_run_finished and wk in self.respondent_threads:
                self.respondent_threads.remove(wk)

        def wk_logger(msg: str, lvl: LogLevels) -> None:
            self.logger.emit(
                msg,
                source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM,
                lvl=lvl,
            )

        wk.signal_info.connect(ret)
        wk.process_msg.connect(wk_logger)
        wk.start()

    def stop_submit(self) -> None:
        """停止所有提交线程"""

        terminated: List[RespondentThread] = []
        for rt in self.respondent_threads:
            if rt.is_alive:
                terminated.append(rt)

            rt.terminate()

        t_ids: List[str] = [f"Tx{rt.currentThreadId()}" for rt in terminated]
        s_t_ids: str = "\n".join(t_ids)

        if not t_ids:
            self.logger.emit(
                "没有正在运行的提交线程",
                source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM,
                lvl="INF",
            )
            return None

        self.respondent_threads.clear()
        self.logger.emit(
            f"提交线程已停止: \n{s_t_ids}",
            source=LogSourceEnum.PROBLEM_SUBMIT_SYSTEM,
            lvl="INF",
        )
        return None

    def at_entry(self) -> None:
        # shared instances
        self.account_manager: AccountManager = SharedInstances.account_manager
        self.logger: BaseLogger = SharedInstances.loggers.o_logger
        self.config: ConfigParams = SharedInstances.config.config

        r = SharedInstances.resource.resource

        qt_state_restore(
            self.remembered_qwidgets,
            r.qt_states,
        )

    def at_exit(self) -> None:
        r = SharedInstances.resource
        store_qt_states(r.resource.qt_states, qt_state_dump(self.remembered_qwidgets))
        r.save()
