import argparse
from pathlib import Path


def add_gui_parser(parser: argparse.ArgumentParser):
    parser.add_argument("--iso", type=Path, help="Automatically load the given ISO")

    from pwime.gui.imgui_main import run_gui
    parser.set_defaults(func=run_gui)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="tool", required=True)
    add_gui_parser(subparsers.add_parser("gui", help="Run the GUI"))

    return parser


def run_cli(argv: list[str]) -> None:
    args = argv[1:]
    if not args:
        args = ["gui"]

    args = create_parser().parse_args(args)
    args.func(args)
