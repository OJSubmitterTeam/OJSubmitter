"""[tools]预提交脚本"""

from scripts.compile_ui import main as compile_ui_main
from tools.code_format import main as code_format_main
from tools.import_sort import main as import_sort_main
from tools.type_check import main as type_check_main


def main() -> None:
    compile_ui_main()
    import_sort_main()
    type_check_main()
    code_format_main()
