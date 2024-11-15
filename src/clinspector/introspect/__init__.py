from __future__ import annotations

import argparse
import importlib.util
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from clinspector.models import commandinfo


def get_cmd_info(
    instance: Any, command: str | None = None
) -> commandinfo.CommandInfo | None:
    """Return a `CommmandInfo` object for command of given instance.

    Instance can be
    - a `Typer` instance
    - **click** `Group` instance
    - An `ArgumentParser` instance
    - A cappa dataclass
    - A cleo Application instance

    Args:
        instance: A supported CLI instance
        command: An optional specific subcommand to fetch info for.
    """
    if importlib.util.find_spec("typer"):
        from clinspector.introspect.introspect_typer import get_info as typer_info
        import typer

        if isinstance(instance, typer.Typer):
            return typer_info(instance, command=command)

    if importlib.util.find_spec("click"):
        from clinspector.introspect.introspect_click import get_info as click_info
        import click

        if isinstance(instance, click.Group):
            return click_info(instance, command=command)

    if importlib.util.find_spec("cleo"):
        from clinspector.introspect.introspect_cleo import get_info as cleo_info
        from cleo.application import Application

        if isinstance(instance, Application):
            return cleo_info(instance, command=command)

    if importlib.util.find_spec("cappa"):
        from clinspector.introspect.introspect_cappa import get_info as cappa_info

        if hasattr(instance, "__cappa__"):
            return cappa_info(instance)  # TODO

    if isinstance(instance, argparse.ArgumentParser):
        from clinspector.introspect.introspect_argparse import get_info as argparse_info

        return argparse_info(instance, command=command)
    return None
