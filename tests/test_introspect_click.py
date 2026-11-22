"""Tests for click introspection."""

from __future__ import annotations

import pytest

from clinspector import get_cmd_info


click = pytest.importorskip("click")


@click.group()
@click.option("-v", "--verbose", count=True, help="Verbosity.")
def cli(verbose: int) -> None:
    """Root command."""


@cli.group()
def grp() -> None:
    """A group."""


@grp.command(hidden=True)
@click.option("--mode", type=click.Choice(["x", "y"]), default="x", envvar=["MODE", "ALT"])
@click.option("--shout/--no-shout", default=False)
@click.argument("files", nargs=-1)
def leaf(mode: str, shout: bool, files: tuple[str, ...]) -> None:
    """A leaf."""


def test_tree():
    info = get_cmd_info(cli)
    assert info
    assert info.name == "cli"
    assert info.description == "Root command."
    assert info.usage == "cli [OPTIONS] COMMAND [ARGS]..."
    assert set(info.subcommands) == {"grp"}
    assert info["grp"]["leaf"].hidden


def test_params():
    info = get_cmd_info(cli, "grp.leaf")
    assert info
    params = {p.name: p for p in info.params}
    assert params["mode"].choices == ["x", "y"]
    assert params["mode"].type == "choice"
    assert params["files"].type == "str"
    assert params["mode"].default == "x"
    assert params["mode"].envvar == "MODE"
    assert params["shout"].secondary_opts == ["--no-shout"]
    assert params["files"].param_type_name == "argument"
    assert params["files"].nargs == -1
    verbose = next(p for p in get_cmd_info(cli).params if p.name == "verbose")  # type: ignore[union-attr]
    assert verbose.count


def test_command_lookup():
    assert get_cmd_info(cli, "grp").name == "grp"  # type: ignore[union-attr]
    assert get_cmd_info(cli, "grp.leaf").name == "leaf"  # type: ignore[union-attr]
    assert get_cmd_info(cli, "cli.grp.leaf").name == "leaf"  # type: ignore[union-attr]
    # unknown commands (e.g. the program name) fall back to the root command
    assert get_cmd_info(cli, "cli").name == "cli"  # type: ignore[union-attr]
    assert get_cmd_info(cli, "nope").name == "cli"  # type: ignore[union-attr]


def test_full_command_and_usage():
    leaf_info = get_cmd_info(cli)["grp"]["leaf"]  # type: ignore[index]
    assert leaf_info.full_command == "cli grp leaf"
    assert leaf_info.usage.startswith("cli grp leaf [OPTIONS]")


def test_plain_command():
    info = get_cmd_info(leaf)
    assert info
    assert info.name == "leaf"
    assert not info.subcommands
