"""Tests for parsing raw help text."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import pytest

from clinspector import parse_help_text


if TYPE_CHECKING:
    import argparse


RESOURCES = pathlib.Path(__file__).parent / "resources"


def _parse(name: str):
    return parse_help_text((RESOURCES / f"{name}.txt").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("name", "prog", "commands"),
    [
        ("argparse", "program.py", ["run", "test", "deploy"]),
        ("cement", "myapp", ["command1", "command2", "command3"]),
        ("cli_click_typer", "cli.py", ["config", "init", "run", "update"]),
        ("cliff", "cliff-app", ["complete", "help", "list", "show", "create", "delete"]),
        ("docopt", "naval_fate.py", []),
        ("fire", "cli.py", ["run", "test", "config"]),
        ("plac", "plac_example.py", ["add", "subtract", "multiply"]),
        ("rich_click", "rich-app", ["config", "init", "run", "status", "version"]),
    ],
)
def test_program_and_commands(name: str, prog: str, commands: list[str]):
    info = _parse(name)
    assert info.name == prog
    assert list(info.subcommands) == commands
    assert info.usage


def test_argparse_layout():
    info = _parse("argparse")
    assert info.description == "Program description"
    assert info["run"].description == "Run the application"
    params = {p.name: p for p in info.params}
    assert params["verbose"].opts == ["-v", "--verbose"]
    assert params["verbose"].is_flag
    assert params["log"].metavar == "FILE"
    assert params["log"].type == "path"
    assert not params["log"].is_flag


def test_click_layout():
    info = _parse("cli_click_typer")
    assert info.description == "A sample CLI built with Click."
    assert info.epilog == "Run 'cli.py COMMAND --help' for more information on a command."
    assert [p.name for p in info.params] == ["version", "debug", "help"]


def test_choices_and_multiline_help():
    params = {p.name: p for p in _parse("rich_click").params}
    assert params["install_completion"].choices == ["bash", "zsh", "fish", "powershell", "pwsh"]
    assert params["install_completion"].help == "Install completion for the specified shell."
    assert params["style"].choices == ["default", "dark", "light"]
    assert params["no_color"].is_flag  # options from extra sections are included


def test_docopt_layout():
    info = _parse("docopt")
    assert info.description == "Naval Fate."
    assert len(info.usage.splitlines()) == 6  # noqa: PLR2004
    speed = next(p for p in info.params if p.name == "speed")
    assert speed.metavar == "kn"
    assert speed.default == "10"
    assert speed.opts == ["--speed"]


def test_single_space_help():
    log_file = next(p for p in _parse("cliff").params if p.name == "log_file")
    assert log_file.metavar == "LOG_FILE"
    assert log_file.help == "Log output to a file"


def test_plac_layout():
    info = _parse("plac")
    number = next(p for p in info.params if p.name == "number")
    assert number.opts == ["-n", "--number"]
    assert number.type == "int"
    assert number.help == "Base number to operate on"
    assert info["add"].description == "Add two numbers"


def test_real_argparse_help(example_argparser: argparse.ArgumentParser):
    example_argparser.prog = "prog"
    info = parse_help_text(example_argparser.format_help())
    assert info.name == "prog"
    params = {p.name: p for p in info.params}
    assert params["input_file"].param_type_name == "argument"
    assert params["input_file"].help == "Input file to process"
    assert params["number"].opts == ["-n", "--number"]
    assert params["mode"].choices == ["fast", "slow", "auto"]
    assert params["enable_feature"].is_flag


def test_ansi_codes_are_stripped():
    text = (
        "\x1b[1;34musage: \x1b[0m\x1b[1;35mprog\x1b[0m [-h]\n\n"
        "options:\n  \x1b[32m-h\x1b[0m  Help.\n"
    )
    info = parse_help_text(text)
    assert info.name == "prog"
    assert info.params[0].opts == ["-h"]


def test_real_click_help():
    click = pytest.importorskip("click")
    from click.testing import CliRunner

    @click.group()
    @click.option("--name", "-n", help="A name.")
    def cli(name: str) -> None:
        """Root help."""

    @cli.command()
    def sub() -> None:
        """Sub help."""

    output = CliRunner().invoke(cli, ["--help"], prog_name="tool").output
    info = parse_help_text(output)
    assert info.name == "tool"
    assert info.description == "Root help."
    assert info["sub"].description == "Sub help."
    name = next(p for p in info.params if p.name == "name")
    assert name.opts == ["-n", "--name"]
    assert name.metavar == "TEXT"
    assert name.type == "str"
