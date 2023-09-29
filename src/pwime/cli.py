import argparse
import typing
from pathlib import Path

from retro_data_structures.game_check import Game


def game_argument_type(s: str) -> Game:
    try:
        return Game(int(s))
    except ValueError:
        # not a number, look by name
        for g in Game:
            g = typing.cast(Game, g)
            if g.name.lower() == s.lower():
                return g
        raise ValueError(f"No enum named {s} found")


def add_gui_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--game",
        type=game_argument_type,
        choices=list(Game),
        default=Game.ECHOES,
        help="Which game to load from target ISO",
    )

    from pwime.gui.imgui_main import run_gui

    parser.set_defaults(func=run_gui)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="tool", required=True)
    add_gui_parser(subparsers.add_parser("gui", help="Run the GUI"))

    return parser


def run_cli(argv: list[str]) -> None:
    argv = argv[1:]
    if not argv:
        argv = ["gui"]

    args = create_parser().parse_args(argv)
    args.func(args)
