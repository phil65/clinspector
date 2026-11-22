"""Tests for typer introspection."""

from __future__ import annotations

from typing import Literal

import pytest
import typer

from clinspector.introspect import get_cmd_info
from clinspector.introspect.introspect_typer import get_info


@pytest.fixture
def app() -> typer.Typer:
    app = typer.Typer(name="tool")

    @app.command()
    def greet(
        name: str,
        count: int = 1,
        loud: bool = typer.Option(False, "--loud", "-l", help="Shout."),
        mode: Literal["a", "b"] = "a",
    ) -> None:
        """Greet someone."""

    @app.command(hidden=True, deprecated=True, epilog="Bye!")
    def secret() -> None:
        """Secret command."""

    return app


def test_subcommands(app: typer.Typer) -> None:
    info = get_info(app)
    assert set(info.subcommands) == {"greet", "secret"}
    assert info.subcommands["greet"].description == "Greet someone."


def test_get_single_command(app: typer.Typer) -> None:
    info = get_info(app, command="greet")
    assert info.name == "greet"
    assert info.usage == "tool greet [OPTIONS] {name}"


def test_params(app: typer.Typer) -> None:
    params = {p.name: p for p in get_info(app, command="greet").params}
    assert set(params) == {"name", "count", "loud", "mode", "help"}

    assert params["name"].param_type_name == "argument"
    assert params["name"].required
    assert params["name"].type == "str"

    assert params["count"].param_type_name == "option"
    assert params["count"].default == 1
    assert params["count"].type == "int"

    assert params["loud"].is_flag
    assert params["loud"].help == "Shout."
    assert set(params["loud"].opts) == {"--loud", "-l"}

    assert params["mode"].choices == ["a", "b"]
    assert params["mode"].type == "choice"
    assert params["loud"].type == "bool"


def test_command_flags(app: typer.Typer) -> None:
    info = get_info(app, command="secret")
    assert info.hidden
    assert info.deprecated
    assert info.epilog == "Bye!"


def test_get_cmd_info_dispatch(app: typer.Typer) -> None:
    info = get_cmd_info(app)
    assert info is not None
    assert set(info.subcommands) == {"greet", "secret"}
