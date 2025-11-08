"""[scripts]构建项目"""

import subprocess
import sys
import time

REMOVED_PACKAGES: list[str] = [
    "mypy",
    "nuitka",
]

rm_cmd = tuple(f"--nofollow-import-to={pkg}" for pkg in REMOVED_PACKAGES)


COMMAND: list[str] = [
    "nuitka",
    "--lto=yes",
    "--standalone",
    "--enable-plugin=pyqt6",
    "--enable-plugin=pylint-warnings",
    "--windows-console-mode=attach",
    "--follow-imports",
    "--output-dir=./dist",
    "--python-flag=-O",
    *rm_cmd,
    "./main.py",
    *sys.argv[1:],
]


def build(mode: str) -> float:
    start_time = time.time()
    try:
        cmd = COMMAND
        print(f"Building with command: {' '.join(cmd)}")
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while building {mode}: {e}")
        sys.exit(1)
    end_time = time.time()
    usage = end_time - start_time

    return usage


def main() -> None:
    usage = build("")
    print(f"{'Build Success':-^50}")
    print(
        f"Build completed in {time.strftime('%H:%M:%S', time.gmtime(usage))} (HH:MM:SS)"
    )
    print(f"-" * 50)
