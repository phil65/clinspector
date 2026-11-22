from __future__ import annotations

import argparse

from clinspector import get_cmd_info


def test_parsing_argumentparser(example_argparser: argparse.ArgumentParser):
    info = get_cmd_info(example_argparser)
    assert info
    assert info.description.startswith("Sample program")
    assert info.epilog
    assert not info.usage.startswith("usage:")


def test_argparse_param_names(example_argparser: argparse.ArgumentParser):
    info = get_cmd_info(example_argparser)
    assert info
    params = {p.name: p for p in info.params}
    assert params["input_file"].param_type_name == "argument"
    assert params["input_file"].required
    assert params["number"].param_type_name == "option"
    assert params["number"].opts == ["-n", "--number"]
    assert params["number"].default == 42  # noqa: PLR2004
    assert params["number"].type == "int"
    assert params["enable_feature"].is_flag
    assert params["mode"].choices == ["fast", "slow", "auto"]
    assert params["verbose"].count
    assert params["verbose"].is_flag
    assert params["help"].is_flag


def _parser_with_subcommands() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool")
    parser.add_argument("--color", action=argparse.BooleanOptionalAction)
    parser.add_argument("--secret", help=argparse.SUPPRESS)
    parser.add_argument("--tag", action="append")
    sub = parser.add_subparsers(dest="cmd")
    build = sub.add_parser("build", aliases=["b"], help="Build things")
    build.add_argument("target")
    nested = build.add_subparsers().add_parser("deep", description="Deep command")
    nested.add_argument("--x")
    sub.add_parser("old", deprecated=True)
    return parser


def test_subcommands():
    info = get_cmd_info(_parser_with_subcommands())
    assert info
    assert set(info.subcommands) == {"build", "old"}  # aliases are skipped
    build = info["build"]
    assert build.name == "build"
    assert build.description == "Build things"
    assert build.full_command == "tool build"
    assert info["old"].deprecated
    assert all(p.name != "==SUPPRESS==" for p in info.params + build.params)
    assert build["deep"].description == "Deep command"


def test_special_actions():
    info = get_cmd_info(_parser_with_subcommands())
    assert info
    params = {p.name: p for p in info.params}
    assert params["color"].opts == ["--color"]
    assert params["color"].secondary_opts == ["--no-color"]
    assert params["color"].is_flag
    assert params["secret"].hidden
    assert params["secret"].help is None
    assert params["tag"].multiple


def test_command_lookup():
    parser = _parser_with_subcommands()
    assert get_cmd_info(parser, "build.deep").name == "deep"  # type: ignore[union-attr]
    assert get_cmd_info(parser, "tool").name == "tool"  # type: ignore[union-attr]
    assert get_cmd_info(parser, "missing").name == "tool"  # type: ignore[union-attr]
