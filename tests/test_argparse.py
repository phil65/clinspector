from __future__ import annotations

from typing import TYPE_CHECKING

from clinspector import get_cmd_info


if TYPE_CHECKING:
    import argparse


def test_parsing_argumentparser(example_argparser: argparse.ArgumentParser):
    info = get_cmd_info(example_argparser)
    assert info
    assert info.description.startswith("Sample program")
