import os
import re
import shutil

root = "."

regexs = [
    r"^.*\.egg-info$",
    r"^__pycache__$",
    r"^\.mypy_cache$",
]


def clean() -> None:
    for dirpath, dirnames, _ in os.walk(root):
        for dirname in dirnames:
            for regex in regexs:
                if re.match(regex, dirname):
                    full_path = os.path.join(dirpath, dirname)
                    print(f"Removing: {full_path}")
                    shutil.rmtree(full_path)
                    break


def main():
    clean()
