from enum import Enum
from typing import Any, Dict, List, Optional

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
)

from ...OJSubmitter.Constant.fields import (
    BTN_ENABLED,
    BTN_TEXT,
    CHECKBOX_CHECKED,
    COMBOX_CURRENT_INDEX,
    COMBOX_CURRENT_TEXT,
    LINEEDIT_TEXT,
    SPIN_VALUE,
)
from ...Util.functiontools import assert_false
from ..Typehint.qt_items import WideRecordableQtWidgetSet


def qt_state_dump(widgets: WideRecordableQtWidgetSet) -> Dict[str, Any]:
    state: Dict[str, Any] = {}

    for widget in widgets:
        widget_name = widget.objectName()
        if widget_name not in state:
            state[widget_name] = {}

        namespace = state[widget_name]

        if isinstance(widget, QCheckBox):
            namespace[CHECKBOX_CHECKED] = widget.isChecked()

        elif isinstance(widget, QComboBox):
            namespace[COMBOX_CURRENT_INDEX] = widget.currentIndex()
            namespace[COMBOX_CURRENT_TEXT] = widget.currentText()

        elif isinstance(widget, QLineEdit):
            namespace[LINEEDIT_TEXT] = widget.text()

        elif isinstance(widget, QPushButton):
            namespace[BTN_ENABLED] = widget.isEnabled()
            namespace[BTN_TEXT] = widget.text()

        elif isinstance(widget, QSpinBox):
            namespace[SPIN_VALUE] = widget.value()

        else:
            assert_false(widget)

    return state


def qt_state_restore(widgets: WideRecordableQtWidgetSet, state: Dict[str, Any]) -> None:
    for widget in widgets:
        widget_name = widget.objectName()
        namespace = state.get(widget_name, {})

        if isinstance(widget, QCheckBox):
            if CHECKBOX_CHECKED in namespace:
                widget.setChecked(namespace[CHECKBOX_CHECKED])

        elif isinstance(widget, QComboBox):
            if COMBOX_CURRENT_INDEX in namespace:
                widget.setCurrentIndex(namespace[COMBOX_CURRENT_INDEX])
            elif COMBOX_CURRENT_TEXT in namespace:
                index = widget.findText(namespace[COMBOX_CURRENT_TEXT])
                if index != -1:
                    widget.setCurrentIndex(index)

        elif isinstance(widget, QLineEdit):
            if LINEEDIT_TEXT in namespace:
                widget.setText(namespace[LINEEDIT_TEXT])

        elif isinstance(widget, QPushButton):
            if BTN_ENABLED in namespace:
                widget.setEnabled(namespace[BTN_ENABLED])
            if BTN_TEXT in namespace:
                widget.setText(namespace[BTN_TEXT])

        elif isinstance(widget, QSpinBox):
            if SPIN_VALUE in namespace:
                widget.setValue(namespace[SPIN_VALUE])

        else:
            assert_false(widget)


def store_qt_states(qt_states: Dict[str, Any], new_states: Dict[str, Any]) -> None:
    for k, v in new_states.items():
        qt_states[k] = v


class MsgBtn(Enum):
    OK = QMessageBox.StandardButton.Ok
    CANCEL = QMessageBox.StandardButton.Cancel
    YES = QMessageBox.StandardButton.Yes
    NO = QMessageBox.StandardButton.No

    @staticmethod
    def from_value(value: QMessageBox.StandardButton) -> "MsgBtn":
        for btn in MsgBtn:
            if btn.value == value:
                return btn
        raise ValueError(f"No matching MsgBtn for value: {value}")


def qt_dialog(
    title: str,
    msg: str,
    btns: Optional[List[MsgBtn]] = [MsgBtn.OK, MsgBtn.CANCEL],
    icon: QMessageBox.Icon = QMessageBox.Icon.Information,
    details: Optional[str] = None,
) -> MsgBtn:
    msg_box = QMessageBox()
    msg_box.setWindowTitle(title)
    msg_box.setIcon(icon)

    msg_box.setText(msg)
    if details is not None:
        msg_box.setDetailedText(details)

    if btns is None:
        btns = []

    union = btns[0].value
    for b in btns[1:]:
        union |= b.value

    if btns:
        msg_box.setStandardButtons(union)

    return MsgBtn.from_value(QMessageBox.StandardButton(msg_box.exec()))
