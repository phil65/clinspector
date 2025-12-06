"""Module for generating Click CLI implementations from CommandInfo objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

    import click

    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


def _create_param(param_info: Param) -> click.Parameter:
    """Convert a Param object to a Click Parameter."""
    import click

    if param_info.opts:  # It's an option
        kwargs: dict[str, Any] = {
            "help": param_info.help,
            "default": param_info.default,
            "required": param_info.required,
            "hidden": param_info.hidden,
            "multiple": param_info.multiple,
            "is_flag": param_info.is_flag,
            "envvar": param_info.envvar,
        }
        if param_info.metavar:
            kwargs["metavar"] = param_info.metavar
        return click.Option(param_info.opts, **kwargs)

    # It's an argument
    kwargs = {"required": param_info.required}
    if param_info.multiple:
        kwargs["nargs"] = -1
    if param_info.metavar:
        kwargs["type"] = click.STRING
    return click.Argument([param_info.name], **kwargs)


def _create_command(
    cmd_info: CommandInfo,
    callback: Callable[..., Any] | None = None,
) -> click.Command:
    """Create a Click Command from a CommandInfo object."""
    import click

    params = [_create_param(p) for p in cmd_info.params]
    return click.Command(
        name=cmd_info.name,
        help=cmd_info.description,
        params=params,
        callback=callback,
        hidden=cmd_info.hidden,
        epilog=cmd_info.epilog,
        deprecated=cmd_info.deprecated,
    )


def create_group(cmd_info: CommandInfo, callback: Callable[..., Any] | None = None) -> click.Group:
    """Create a Click Group from a CommandInfo object.

    Args:
        cmd_info: The CommandInfo object to convert
        callback: Optional callback function for the group

    Returns:
        A Click Group object with all commands and subcommands
    """
    import click

    group = click.Group(
        name=cmd_info.name,
        help=cmd_info.description,
        params=[_create_param(p) for p in cmd_info.params],
        callback=callback,
        epilog=cmd_info.epilog,
        deprecated=cmd_info.deprecated,
    )

    # Add all subcommands recursively
    for subcmd in cmd_info.subcommands.values():
        cmd = create_group(subcmd) if subcmd.subcommands else _create_command(subcmd)
        group.add_command(cmd)
    return group


if __name__ == "__main__":
    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param

    # Example usage
    info = CommandInfo(
        name="mycli",
        description="A sample CLI",
        params=[
            Param(name="verbose", help="Increase verbosity", is_flag=True, opts=["-v", "--verbose"])
        ],
        subcommands={
            "hello": CommandInfo(
                name="hello",
                description="Say hello",
                params=[Param(name="name", help="Name to greet", required=True)],
            )
        },
    )

    cli = create_group(info)
    cli()
