"""[tools]帮助信息显示"""

import os
import tomllib


def get_script_map(pyproject_path: str) -> dict[str, str]:
    with open(pyproject_path, "rb") as f:
        toml_data = tomllib.load(f)
    scripts = toml_data.get("project", {}).get("scripts", {})
    script_map: dict[str, str] = {}
    for cmd, entry in scripts.items():
        # entry 格式如 "scripts.type_check:main"
        module_path = entry.split(":")[0].replace(".", "/") + ".py"
        script_map[cmd] = module_path
    return script_map


def get_docstring(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            doc = line.strip().strip('"""').strip("'''")
            return doc
    return "(无说明)"


def get_help_lines(script_map: dict[str, str]) -> list[str]:
    help_lines: list[str] = []
    for cmd, path in script_map.items():
        abs_path = os.path.join(os.path.dirname(__file__), "..", path)
        doc = get_docstring(file_path=abs_path)
        right = doc.index("]")
        help_lines.append(
            f"uv run {cmd:<10} - {doc[:right + 1]}\t{doc[right + 1:].strip()}"
        )
    return help_lines


def get_proj_name() -> str:
    with open("pyproject.toml", "rb") as f:
        toml_data = tomllib.load(f)
    return toml_data.get("project", {}).get("name", "Unknown Project")


HELP_HEAD: str = f"""\
这是 {get_proj_name()} 项目的命令行工具帮助信息。
你可以使用以下命令来执行不同的脚本和工具：
"""


def main() -> None:
    script_map = get_script_map(pyproject_path="pyproject.toml")
    help_lines = get_help_lines(script_map=script_map)
    help_message = HELP_HEAD + "\n".join(help_lines)
    print(help_message)
