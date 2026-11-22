"""Tests for cleo introspection."""

from __future__ import annotations

from typing import ClassVar

import pytest

from clinspector import get_cmd_info


pytest.importorskip("cleo")

from cleo.application import Application
from cleo.commands.command import Command
from cleo.helpers import argument, option


class GreetCommand(Command):
    name = "greet"
    description = "Greets someone"
    arguments: ClassVar = [argument("who", description="Who to greet", optional=True)]
    options: ClassVar = [option("yell", "y", description="Yell", flag=True)]

    def handle(self) -> int:
        return 0


class CacheClearCommand(Command):
    name = "cache clear"
    description = "Clear the cache"

    def handle(self) -> int:
        return 0


@pytest.fixture
def app() -> Application:
    app = Application(name="tool")
    app.add(GreetCommand())
    app.add(CacheClearCommand())
    return app


def test_commands(app: Application):
    info = get_cmd_info(app)
    assert info
    assert info.name == "tool"
    assert {"greet", "cache clear"} <= set(info.subcommands)
    assert "list" not in info.subcommands


def test_params(app: Application):
    info = get_cmd_info(app, "greet")
    assert info
    assert info.description == "Greets someone"
    assert info.usage.startswith("greet")
    params = {p.name: p for p in info.params}
    assert params["who"].param_type_name == "argument"
    assert not params["who"].required
    assert params["yell"].opts == ["-y", "--yell"]
    assert params["yell"].is_flag


def test_lookup_with_spaces(app: Application):
    assert get_cmd_info(app, "cache clear").name == "cache clear"  # type: ignore[union-attr]
