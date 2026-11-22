"""Module for generating Click CLI implementations from CommandInfo objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from clinspector.synthesis import is_help_param


if TYPE_CHECKING:
    from clinspector.synthesis import Handler


if TYPE_CHECKING:
    from collections.abc import Callable

    import click

    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


def _create_param(param_info: Param) -> click.Parameter:
    """Convert a Param object to a Click Parameter."""
    import click

    kwargs: dict[str, Any] = {}
    if param_info.choices:
        kwargs["type"] = click.Choice(param_info.choices)
    if param_info.metavar:
        kwargs["metavar"] = param_info.metavar

    if param_info.opts:  # It's an option
        decls = list(param_info.opts)
        if param_info.secondary_opts:
            decls = [f"{decls[0]}/{param_info.secondary_opts[0]}", *decls[1:]]
        kwargs.update(
            help=param_info.help,
            required=param_info.required,
            hidden=param_info.hidden,
            multiple=param_info.multiple,
            envvar=param_info.envvar,
        )
        if param_info.default is not None:
            kwargs["default"] = param_info.default
        if param_info.count:
            kwargs["count"] = True
        elif param_info.is_flag and not param_info.secondary_opts:
            kwargs["is_flag"] = True
        return click.Option([param_info.name, *decls], **kwargs)

    # It's an argument
    kwargs["required"] = param_info.required
    if param_info.multiple or param_info.nargs == -1:
        kwargs["nargs"] = -1
    elif isinstance(param_info.nargs, int) and param_info.nargs > 1:
        kwargs["nargs"] = param_info.nargs
    if param_info.default is not None and not param_info.required:
        kwargs["default"] = param_info.default
    return click.Argument([param_info.name], **kwargs)


def _create_params(cmd_info: CommandInfo) -> list[click.Parameter]:
    return [_create_param(p) for p in cmd_info.params if not is_help_param(p)]


def _callback(cmd_info: CommandInfo, handler: Handler | None) -> Callable[..., Any] | None:
    if handler is None:
        return None

    def callback(**kwargs: Any) -> Any:
        return handler(cmd_info, kwargs)

    return callback


def _create_command(cmd_info: CommandInfo, handler: Handler | None = None) -> click.Command:
    """Create a Click Command from a CommandInfo object."""
    import click

    return click.Command(
        name=cmd_info.name,
        help=cmd_info.description,
        params=_create_params(cmd_info),
        callback=_callback(cmd_info, handler),
        hidden=cmd_info.hidden,
        epilog=cmd_info.epilog,
        deprecated=cmd_info.deprecated,
    )


def create_group(cmd_info: CommandInfo, handler: Handler | None = None) -> click.Group:
    """Create a Click Group from a CommandInfo object.

    Args:
        cmd_info: The CommandInfo object to convert
        handler: Called with the invoked (sub)command's info and its parsed values.
                 Groups are invoked before their subcommands, as usual for click.

    Returns:
        A Click Group object with all commands and subcommands
    """
    import click

    group = click.Group(
        name=cmd_info.name,
        help=cmd_info.description,
        params=_create_params(cmd_info),
        callback=_callback(cmd_info, handler),
        hidden=cmd_info.hidden,
        epilog=cmd_info.epilog,
        deprecated=cmd_info.deprecated,
    )

    # Add all subcommands recursively
    for name, subcmd in cmd_info.subcommands.items():
        cmd = (
            create_group(subcmd, handler)
            if subcmd.subcommands
            else _create_command(subcmd, handler)
        )
        group.add_command(cmd, name=name)
    return group
