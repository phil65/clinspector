import pytest

from clinspector.introspect.markdown import get_cmd_markdown


click = pytest.importorskip("click")
pytest.importorskip("minijinja")


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


@cli.group()
def grp() -> None:
    """A group."""


@grp.command()
@click.option("--retries", default=0, help="Retries")
@click.option("--secret", hidden=True, help="Hidden option")
@click.option("--level", type=click.Choice(["a", "b"]), help="Level <name>")
def deep(retries: int, secret: str, level: str) -> None:
    """Deep command."""


@grp.command(hidden=True)
def invisible() -> None:
    """Hidden command."""


def test_get_cmd_markdown_nested():
    text = get_cmd_markdown(cli, include_subcommands=True)
    assert "# deep" in text
    assert "# invisible" not in text


def test_get_cmd_markdown_params():
    text = get_cmd_markdown(cli, "grp.deep")
    assert "**Default:** 0" in text
    assert "Hidden option" not in text
    assert "**Choices:** a, b" in text
    assert "Level <name>" in text  # no HTML escaping


def test_get_cmd_markdown_argument_heading():
    text = get_cmd_markdown(cli, "build")
    assert "### TARGET" in text


def test_get_cmd_markdown_required_multiple_envvar():
    @click.command()
    @click.option("--tag", multiple=True, envvar="APP_TAG", required=True, help="Tags")
    def deploy(tag: tuple[str, ...]) -> None:
        """Deploy app."""

    text = get_cmd_markdown(deploy)
    tag_section = text.split("### `--help`")[0]
    assert "**REQUIRED**" in tag_section
    assert "Environment variable: APP_TAG" in tag_section
    assert "**Multiple values allowed.**" in tag_section
    assert "**Default:**" not in tag_section
