"""[tools]导入排序工具"""

import subprocess
import sys
from typing import List


def main() -> None:
    cmd: List[str] = ["isort", "."]

    extra_args = sys.argv[1:]
    if extra_args:
        cmd.extend(extra_args)

    print("Running command:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running '{' '.join(cmd)}': {e}")
        sys.exit(1)
