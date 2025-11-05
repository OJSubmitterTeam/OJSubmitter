"""[scripts]编译:UI2PY"""

import pathlib

from PyQt6.uic import pyuic


def compile_ui(input_file: str, output_file: str) -> None:
    pyuic.generate(input_file, output_file, indent=4, execute=False)  # type: ignore[no-untyped-call]


def rm_ui_headers() -> None:
    """移除所有UI文件头部注释"""
    root = r"src/GUI/UI"
    ui_path = pathlib.Path(root)
    # list files
    files = ui_path.rglob("UI_*.py")
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 找到第一个非注释行的索引
        first_non_comment_index = 0
        for i, line in enumerate(lines):
            if not line.strip().startswith("#") and line.strip() != "":
                first_non_comment_index = i
                break

        # 移除头部注释
        lines = lines[first_non_comment_index:]
        with open(file, "w", encoding="utf-8") as f:
            f.writelines(lines)


def main() -> None:
    compile_ui("src/GUI/UI/main.ui", "src/GUI/UI/UI_main.py")
    rm_ui_headers()
