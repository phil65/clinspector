"""Round-trip tests: CommandInfo -> framework app -> CommandInfo."""

from __future__ import annotations

from typing import Any

import pytest

from clinspector import CommandInfo, Param, get_cmd_info


def _info() -> CommandInfo:
    build_params = [
        Param(name="target", param_type_name="argument", required=True, help="Target"),
        Param(name="mode", opts=["--mode"], choices=["fast", "slow"], default="fast"),
        Param(name="tag", opts=["-t", "--tag"], multiple=True, help="Tags"),
        Param(name="dry_run", opts=["--dry-run"], is_flag=True, help="Dry run"),
    ]
    root_params = [Param(name="verbose", opts=["-v", "--verbose"], is_flag=True, count=True)]
    build = CommandInfo(name="build", description="Build it.", params=build_params)
    return CommandInfo(
        name="tool", description="Tool.", params=root_params, subcommands={"build": build}
    )


def _check_roundtrip(app: Any, *, choices: bool = True) -> None:
    info = get_cmd_info(app)
    assert info
    assert info.name == "tool"
    build = info["build"]
    assert build.description == "Build it."
    params = {p.name.replace("-", "_"): p for p in build.params}
    assert params["target"].param_type_name == "argument"
    assert params["target"].required
    assert params["mode"].opts == ["--mode"]
    if choices:
        assert params["mode"].choices == ["fast", "slow"]
    assert params["tag"].multiple
    assert set(params["tag"].opts) == {"-t", "--tag"}
    assert params["dry_run"].is_flag


def test_click():
    pytest.importorskip("click")
    from clinspector.synthesis.synth_click import create_group

    _check_roundtrip(create_group(_info()))


def test_typer():
    pytest.importorskip("typer")
    from typer.testing import CliRunner

    from clinspector.synthesis.synth_typer import create_app

    received: dict[str, Any] = {}
    app = create_app(_info(), callback=lambda **kw: received.update(kw))
    _check_roundtrip(app)
    result = CliRunner().invoke(app, ["-vv", "build", "x", "--tag", "a", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert received == {"verbose": 2}
    assert "'tag': ['a']" in result.output


def test_argparse():
    from clinspector.synthesis.synth_argparse import create_parser

    parser = create_parser(_info())
    _check_roundtrip(parser)
    ns = parser.parse_args(["-vv", "build", "x", "-t", "a", "-t", "b", "--dry-run"])
    assert ns.verbose == 2  # noqa: PLR2004
    assert ns.tag == ["a", "b"]
    assert ns.dry_run
    assert ns.mode == "fast"


def test_cleo():
    pytest.importorskip("cleo")
    from clinspector.synthesis.synth_cleo import create_app

    _check_roundtrip(create_app(_info()), choices=False)  # cleo has no choices


def test_cappa():
    cappa = pytest.importorskip("cappa")
    from clinspector.synthesis.synth_cappa import create_class

    cls = create_class(_info())
    _check_roundtrip(cls)
    parsed = cappa.parse(cls, argv=["-v", "build", "x", "--mode", "slow", "-t", "a"])
    assert parsed.verbose == 1
    assert parsed.subcommand.target == "x"
    assert parsed.subcommand.mode == "slow"
    assert parsed.subcommand.tag == ["a"]
