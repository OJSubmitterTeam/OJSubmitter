from typing import Any, Set, TypeAlias, Union

from PyQt6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QPushButton, QSpinBox

RecordableQtWidget: TypeAlias = Union[
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
]


RecordableQtWidgetSet = Set[RecordableQtWidget]
WideRecordableQtWidgetSet: TypeAlias = Union[RecordableQtWidgetSet, Any]
