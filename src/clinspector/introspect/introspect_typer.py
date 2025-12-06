from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from typer.main import get_command

from clinspector.introspect import introspect_click


if TYPE_CHECKING:
    from clinspector.models import commandinfo


def get_info(instance: typer.Typer, command: str | None = None) -> commandinfo.CommandInfo:
    """Return a `CommmandInfo` object for command of given Typer object.

    Args:
        instance: A `Typer`, **click** `Group` or `ArgumentParser` instance
        command: The command to get info for.
    """
    cmd = get_command(instance)
    info = introspect_click.parse(cmd)
    if command:
        ctx = typer.Context(cmd)
        subcommands = getattr(cmd, "commands", {})
        cmds = {k: introspect_click.parse(v, parent=ctx) for k, v in subcommands.items()}
        return cmds.get(command, info)
    return info


if __name__ == "__main__":
    from mkdocs_mknodes import cli

    info = get_info(cli.cli, command="mkdocs")
    print(info)
