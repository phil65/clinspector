"""Tests for cappa introspection."""

from dataclasses import dataclass
from typing import Annotated

import pytest

from clinspector import get_cmd_info


cappa = pytest.importorskip("cappa")


@cappa.command(name="sub", help="Sub command.")
@dataclass
class Sub:
    tags: Annotated[list[str], cappa.Arg(long=True, choices=["a", "b"])]
    token: Annotated[str | None, cappa.Arg(long=True, default=cappa.Env("TOKEN"))] = None
    verbose: Annotated[int, cappa.Arg(short=True, count=True)] = 0


@cappa.command(name="tool")
@dataclass
class Tool:
    """Tool command."""

    name: Annotated[str, cappa.Arg(help="A name")]
    count: Annotated[int, cappa.Arg(short="-c", long=True, help="Times")] = 1
    loud: Annotated[bool, cappa.Arg(short=True)] = False
    cmd: cappa.Subcommands[Sub | None] = None


def test_command():
    info = get_cmd_info(Tool)
    assert info
    assert info.name == "tool"
    assert info.description == "Tool command."
    assert set(info.subcommands) == {"sub"}
    assert info.usage == "tool [OPTIONS] NAME COMMAND"


def test_params():
    info = get_cmd_info(Tool)
    assert info
    params = {p.name: p for p in info.params}
    assert set(params) == {"name", "count", "loud"}
    assert params["name"].param_type_name == "argument"
    assert params["name"].required
    assert params["name"].help == "A name"
    assert params["count"].opts == ["-c", "--count"]
    assert params["count"].default == 1
    assert params["count"].type == "int"
    assert params["name"].type == "str"
    assert params["loud"].is_flag
    assert params["loud"].opts == ["-l", "--loud"]


def test_subcommand_params():
    info = get_cmd_info(Tool, "sub")
    assert info
    assert info.full_command == "tool sub"
    params = {p.name: p for p in info.params}
    assert params["tags"].multiple
    assert params["tags"].choices == ["a", "b"]
    assert params["tags"].type == "str"
    assert params["token"].envvar == "TOKEN"
    assert params["verbose"].count
