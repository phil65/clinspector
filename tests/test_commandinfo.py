from __future__ import annotations

from clinspector import CommandInfo, Param


def _info() -> CommandInfo:
    params = [
        Param(name="target", param_type_name="argument"),
        Param(name="tag", opts=["-t", "--tag"], multiple=True),
        Param(name="verbose", opts=["-v"], is_flag=True, count=True),
        Param(name="color", opts=["--color"], secondary_opts=["--no-color"], is_flag=True),
        Param(name="dry_run", opts=["--dry-run"], is_flag=True),
        Param(name="mode", opts=["--mode"]),
    ]
    sub = CommandInfo(name="build", params=params)
    return CommandInfo(name="tool", subcommands={"build": sub})


def test_full_path():
    info = _info()
    assert info["build"].full_path == ["tool", "build"]
    assert info.subcommands["build"].full_command == "tool build"


def test_build_cli_command():
    build = _info()["build"]
    args = {
        "target": "x",
        "tag": ["a", "b"],
        "verbose": 2,
        "color": False,
        "dry_run": False,
        "mode": "fast",
    }
    assert build.build_cli_command(args) == [
        *("tool", "build", "x"),
        *("-t", "a", "-t", "b"),
        *("-v", "-v"),
        "--no-color",
        *("--mode", "fast"),
    ]
    assert build.build_cli_command({"verbose": True, "dry_run": True}) == [
        *("tool", "build", "-v", "--dry-run"),
    ]
    assert build.build_cli_command() == ["tool", "build"]


def test_to_dict_roundtrip():
    import json

    info = _info()
    info.callback = print
    data = info.to_dict()
    assert "callback" not in data
    json.dumps(data)  # serializable
    restored = CommandInfo.from_dict(data)
    assert restored == info  # callbacks and parent links are not compared
    assert restored["build"].full_command == "tool build"
    assert restored["build"].params[1].multiple


def test_walk():
    assert [c.full_command for c in _info().walk()] == ["tool", "tool build"]


def test_param_from_dict_ignores_unknown_keys():
    param = Param.from_dict({"name": "x", "opts": ["--x"], "unknown": 1})
    assert param.name == "x"
    assert param.is_option
