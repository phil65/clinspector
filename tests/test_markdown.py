from __future__ import annotations

import pytest

from clinspector.introspect.markdown import get_cmd_markdown


click = pytest.importorskip("click")
pytest.importorskip("jinja2")


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose: bool) -> None:
    """Example CLI tool."""


@cli.command()
@click.argument("target")
def build(target: str) -> None:
    """Build the project."""


def test_get_cmd_markdown():
    text = get_cmd_markdown(cli)
    assert "# cli" in text
    assert "Example CLI tool." in text
    assert "`--verbose`, `-v`" in text
    assert "Enable verbose output" in text
    assert "# build" not in text


def test_get_cmd_markdown_with_subcommands():
    text = get_cmd_markdown(cli, include_subcommands=True)
    assert "# build" in text
    assert "Build the project." in text


def test_get_cmd_markdown_single_command():
    text = get_cmd_markdown(cli, "build")
    assert "# build" in text
