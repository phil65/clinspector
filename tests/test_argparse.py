from __future__ import annotations

from typing import TYPE_CHECKING

from clinspector import get_cmd_info


if TYPE_CHECKING:
    import argparse


def test_parsing_argumentparser(example_argparser: argparse.ArgumentParser):
    info = get_cmd_info(example_argparser)
    assert info
    assert info.description.startswith("Sample program")


def test_argparse_param_names(example_argparser: argparse.ArgumentParser):
    info = get_cmd_info(example_argparser)
    assert info
    params = {p.name: p for p in info.params}
    assert params["input_file"].param_type_name == "argument"
    assert params["number"].param_type_name == "option"
    assert params["number"].opts == ["-n", "--number"]
    assert params["number"].default == 42  # noqa: PLR2004
