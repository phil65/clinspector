"""Introspection module for cyclopts CLI applications."""

from __future__ import annotations

import inspect
import types
import typing
from typing import TYPE_CHECKING, Any

from cyclopts.command_spec import CommandSpec

from clinspector.introspect._utils import annotation_type_name, first_envvar, resolve_command
from clinspector.models import commandinfo, param


if TYPE_CHECKING:
    from cyclopts import App
    from cyclopts.argument import Argument


def _parse_argument(argument: Argument) -> param.Param:
    """Convert a cyclopts `Argument` into a `Param`."""
    field_info = argument.field_info
    positional = argument.is_positional_only() or argument.is_var_positional()
    names = list(argument.names)
    negatives = list(argument.negatives)
    opts = [] if positional else [n for n in names if n not in negatives]
    default = field_info.default
    choices = argument.get_choices()
    hint = argument.hint
    multiple = argument.is_var_positional() or typing.get_origin(_strip_optional(hint)) in (
        list,
        set,
        tuple,
        frozenset,
    )
    return param.Param(
        name=field_info.name,
        help=argument.parameter.help or None,
        default=None if default is inspect.Parameter.empty else default,
        required=bool(argument.required),
        opts=opts,
        secondary_opts=negatives if not positional else [],
        is_flag=argument.is_flag(),
        param_type_name="argument" if positional else "option",
        multiple=multiple,
        nargs=-1 if multiple and positional else 1,
        hidden=not argument.show,
        metavar=names[0] if positional and names else None,
        envvar=first_envvar(argument.parameter.env_var),
        choices=[str(c) for c in choices] if choices else None,
        type=annotation_type_name(hint),
    )


def _strip_optional(hint: Any) -> Any:
    args = [a for a in typing.get_args(hint) if a is not type(None)]
    if typing.get_origin(hint) in (typing.Union, types.UnionType) and len(args) == 1:
        return args[0]
    return hint


def _extract_params_from_app(app: App) -> list[param.Param]:
    """Extract parameters from a cyclopts App's default command."""
    if not app.default_command:
        return []
    collection = app.assemble_argument_collection(parse_docstring=True)
    return [_parse_argument(argument) for argument in collection if not argument.children]


def _parse_app(app: App, parent_name: str = "") -> commandinfo.CommandInfo:
    """Parse a cyclopts App into a CommandInfo object.

    Args:
        app: Cyclopts App instance
        parent_name: Name of parent command for building full paths

    Returns:
        CommandInfo object
    """
    # Get app name - cyclopts apps can have multiple names via tuples
    name = app.name[0] if app.name else ""
    # Build full name including parent
    full_name = f"{parent_name} {name}".strip() if parent_name else name
    usage = app.usage if app.usage else full_name  # Get usage string

    # Extract parameters from default command
    params = _extract_params_from_app(app)

    # Parse subcommands
    subcommands = {}
    for cmd_name, sub_app in app._commands.items():
        # Skip help and version commands
        if (cmd_name in app.help_flags) or (cmd_name in app.version_flags):
            continue
        try:
            if isinstance(sub_app, CommandSpec):
                resolved = sub_app.resolve(app)
                sub_info = _parse_app(resolved, full_name)
            else:
                sub_info = _parse_app(sub_app, full_name)
            subcommands[cmd_name] = sub_info
        except AttributeError, TypeError, ValueError:
            # Create minimal command info for problematic subcommands
            subcommands[cmd_name] = commandinfo.CommandInfo(name=cmd_name)

    return commandinfo.CommandInfo(
        name=name,
        description=app.help,
        usage=usage,
        params=params,
        subcommands=subcommands,
        hidden=not app.show,
        epilog=getattr(app, "epilog", None),
        callback=app.default_command,
    )


def get_info(instance: App, command: str | None = None) -> commandinfo.CommandInfo:
    """Return a CommandInfo object for command of given cyclopts App.

    Args:
        instance: A cyclopts App instance
        command: The command to get info for (supports dot notation for subcommands)

    Returns:
        CommandInfo object with extracted information
    """
    return resolve_command(_parse_app(instance), command)
