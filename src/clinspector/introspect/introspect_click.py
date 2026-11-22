from __future__ import annotations

import dataclasses
from typing import Any

import click

from clinspector.introspect._utils import first_envvar, resolve_command
from clinspector.models import commandinfo, param


_PARAM_FIELDS = {f.name for f in dataclasses.fields(param.Param)}


def _parse_param(p: click.Parameter) -> param.Param:
    """Convert a click `Parameter` into a `Param`."""
    dct: dict[str, Any] = {k: v for k, v in p.to_info_dict().items() if k in _PARAM_FIELDS}
    choices = getattr(p.type, "choices", None)
    dct["envvar"] = first_envvar(p.envvar)
    dct["choices"] = [str(c) for c in choices] if choices is not None else None
    dct["metavar"] = p.metavar
    dct["is_eager"] = p.is_eager
    dct.setdefault("hidden", getattr(p, "hidden", False))
    return param.Param(**dct)


def parse(
    command: click.Command,
    parent: click.Context | None = None,
) -> commandinfo.CommandInfo:
    """Get a `CommandInfo` dataclass for given click `Command`.

    Args:
        command: The **click** `Command` to get info for.
        parent: The optional parent context
    """
    ctx = click.Context(command, parent=parent)
    subcommands = getattr(command, "commands", {})
    formatter = ctx.make_formatter()
    pieces = command.collect_usage_pieces(ctx)
    formatter.write_usage(ctx.command_path, " ".join(pieces), prefix="")
    usage = formatter.getvalue().rstrip("\n")
    # Generate the full usage string based on parents if any, i.e. `root sub1 sub2 ...`.
    full_path = []
    current: click.Context | None = ctx
    while current is not None:
        name = current.command.name.lower() if current.command.name else ""
        full_path.append(name)
        current = current.parent
    full_path.reverse()
    return commandinfo.CommandInfo(
        name=command.name or "",
        description=command.help or command.short_help or "",
        usage=" ".join(full_path) + usage,
        params=[_parse_param(p) for p in command.get_params(ctx)],
        subcommands={k: parse(v, parent=ctx) for k, v in subcommands.items()},
        deprecated=bool(command.deprecated),
        epilog=command.epilog,
        hidden=command.hidden,
        callback=command.callback,
    )


def get_info(
    instance: click.Command,
    command: str | None = None,
) -> commandinfo.CommandInfo:
    """Return a `CommandInfo` object for command of given click Command / Group.

    Args:
        instance: A **click** `Command` or `Group` instance
        command: The command to get info for (supports dot notation for subcommands).
    """
    return resolve_command(parse(instance), command)
