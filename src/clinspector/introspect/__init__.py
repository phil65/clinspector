from __future__ import annotations

import argparse
import importlib.util
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from clinspector.models import commandinfo


def get_cmd_info(  # noqa: PLR0911
    instance: Any, command: str | None = None
) -> commandinfo.CommandInfo | None:
    """Return a `CommandInfo` object for command of given instance.

    Instance can be
    - a `Typer` instance
    - a **click** `Command` / `Group` instance
    - a cleo `Application` instance
    - a cappa command class
    - a cyclopts `App` instance
    - an `ArgumentParser` instance

    Args:
        instance: A supported CLI instance
        command: An optional subcommand to fetch info for. Nested subcommands can be
                 addressed with dot notation (`"group.subcommand"`). If the subcommand
                 does not exist, info for the root command is returned.

    Returns:
        The command info, or None if the instance type is not supported.
    """
    if importlib.util.find_spec("typer"):
        import typer

        if isinstance(instance, typer.Typer):
            from clinspector.introspect.introspect_typer import get_info as typer_info

            return typer_info(instance, command=command)

    if importlib.util.find_spec("click"):
        import click

        if isinstance(instance, click.Command):
            from clinspector.introspect.introspect_click import get_info as click_info

            return click_info(instance, command=command)

    if importlib.util.find_spec("cleo"):
        from cleo.application import Application

        if isinstance(instance, Application):
            from clinspector.introspect.introspect_cleo import get_info as cleo_info

            return cleo_info(instance, command=command)

    if importlib.util.find_spec("cappa") and hasattr(instance, "__cappa__"):
        from clinspector.introspect.introspect_cappa import get_info as cappa_info

        return cappa_info(instance, command=command)

    if importlib.util.find_spec("cyclopts"):
        import cyclopts

        if isinstance(instance, cyclopts.App):
            from clinspector.introspect.introspect_cyclopts import get_info as cyclopts_info

            return cyclopts_info(instance, command=command)

    if isinstance(instance, argparse.ArgumentParser):
        from clinspector.introspect.introspect_argparse import get_info as argparse_info

        return argparse_info(instance, command=command)
    return None
