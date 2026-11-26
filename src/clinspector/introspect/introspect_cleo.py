"""Module for inspecting Cleo CLI applications."""

from typing import TYPE_CHECKING

from clinspector.introspect._utils import resolve_command
from clinspector.models import commandinfo, param


if TYPE_CHECKING:
    from cleo.application import Application
    from cleo.commands.command import Command


def _parse_command(command: Command, name: str | None = None) -> commandinfo.CommandInfo:
    """Parse a Cleo Command into a CommandInfo object."""
    definition = command.definition
    params = [
        param.Param(
            name=argument.name,
            help=argument.description or None,
            default=argument.default,
            required=argument.is_required(),
            param_type_name="argument",
            multiple=argument.is_list(),
            nargs=-1 if argument.is_list() else 1,
        )
        for argument in definition.arguments
    ] + [
        param.Param(
            name=option.name,
            help=option.description or None,
            default=option.default,
            opts=[f"-{s}" for s in (option.shortcut or "").split("|") if s] + [f"--{option.name}"],
            is_flag=option.is_flag(),
            multiple=option.is_list(),
            param_type_name="option",
        )
        for option in definition.options
    ]
    cmd_name = name or command.name or ""
    return commandinfo.CommandInfo(
        name=cmd_name,
        description=command.description,
        usage=command.synopsis().strip() or cmd_name,
        params=params,
        hidden=command.hidden,
        callback=command.handle,
    )


def parse(app: Application) -> commandinfo.CommandInfo:
    """Parse a Cleo Application into a CommandInfo object."""
    default_cmd_name = app._default_command  # usually "list"
    commands = app.all()  # also resolves lazily loaded commands
    sub_cmds = {
        n: _parse_command(cmd, name=n) for n, cmd in commands.items() if n != default_cmd_name
    }
    default_cmd = commands.get(default_cmd_name)
    return commandinfo.CommandInfo(
        name=app.name or "",
        description="",
        usage=f"{app.name} [options] [--] <command> [<arguments>]",
        subcommands=sub_cmds,
        params=_parse_command(default_cmd).params if default_cmd else [],
    )


def get_info(instance: Application, command: str | None = None) -> commandinfo.CommandInfo:
    """Return a CommandInfo object for command of given Cleo Application.

    Args:
        instance: A Cleo Application instance
        command: The command to get info for (e.g. `"cache clear"`).
    """
    return resolve_command(parse(instance), command)
