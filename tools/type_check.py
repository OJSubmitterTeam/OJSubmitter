import subprocess

# e.g., UI_main.py
excludes = [r"^.*UI_.*\.py$"]

mypy_command: list[str] = [
    "mypy",
    "src",
    "--strict",
    "--follow-imports=silent",
    "--exclude",
    *excludes,
]


def main() -> None:
    print("Running type check...")
    print("mypy command:", " ".join(mypy_command))
    subprocess.run(mypy_command)
