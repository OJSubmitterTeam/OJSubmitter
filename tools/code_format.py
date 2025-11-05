"""[tools]代码格式化工具"""

import subprocess
import sys

COMMANDS: list[list[str]] = [
    ["isort ."],
    ["black", "**/*.py"],
]


def main() -> None:
    for cmd in COMMANDS:
        full_cmd = " ".join(cmd)
        print(f"Running command: {full_cmd}")
        try:
            subprocess.run(full_cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running '{full_cmd}': {e}")
            sys.exit(1)
