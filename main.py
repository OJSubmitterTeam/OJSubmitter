"""[src]入口主程序"""

import argparse
import sys
from typing import List, Optional

from src.CLI import cli_main
from src.GUI import gui_main


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the OJSubmitter application.")
    parser.add_argument(
        "--mode",
        choices=["CLI", "GUI"],
        default="GUI",
        help="Choose the mode to run the application: CLI or GUI (default: CLI)",
    )
    args, unknown = parser.parse_known_args(argv)
    args.unknown_args = unknown
    return args


def main() -> None:
    args: argparse.Namespace = parse_args(sys.argv[1:])
    if args.mode == "CLI":
        cli_main()
    elif args.mode == "GUI":
        gui_main()


if __name__ == "__main__":
    main()
