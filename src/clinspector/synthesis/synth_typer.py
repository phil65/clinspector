"""Module for generating Typer CLI implementations from CommandInfo objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import typer


if TYPE_CHECKING:
    from collections.abc import Callable

    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


def _param_to_option(param: Param) -> dict[str, Any]:
    """Convert a Param to Typer Option arguments."""
    kwargs: dict[str, Any] = {
        "help": param.help,
        "default": param.default,
        "hidden": param.hidden,
        "envvar": param.envvar,
    }

    if param.multiple:
        kwargs["multiple"] = True
    if param.is_flag:
        kwargs["is_flag"] = True
    if param.required and param.default is None:
        # For required parameters without default, use ... with param name
        kwargs["default"] = typer.Option(param.name, required=True)  # type: ignore
    if param.metavar:
        kwargs["metavar"] = param.metavar

    return kwargs


def _create_callback(
    cmd_info: CommandInfo,
    app: typer.Typer,
) -> Callable[..., Any]:
    """Create a callback function for a command."""
    params = []
    for param in cmd_info.params:
        # Use Any as base for param_type to allow both str and list[str]
        param_type: type[str | list[str] | bool] = str  # Default type
        if param.opts:
            # It's an option - use typer.Option
            option_kwargs = _param_to_option(param)
            del option_kwargs["default"]  # Remove default from kwargs
            if param.multiple:
                param_type = list[str]  # type: ignore
            elif param.is_flag:
                param_type = bool
            default_or_param = typer.Option(param.default, *param.opts, **option_kwargs)
        else:
            # It's an argument - use typer.Argument
            arg_kwargs = {
                "help": param.help,
                "hidden": param.hidden,
            }
            if param.multiple:
                param_type = list[str]  # type: ignore
            default_or_param = typer.Argument(param.default, **arg_kwargs)  # type: ignore

        import inspect

        params.append(
            inspect.Parameter(
                name=param.name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default_or_param,
                annotation=param_type,
            )
        )

    # Create a dynamic function with the correct signature
    def callback(*args: Any, **kwargs: Any) -> int:
        # This is a placeholder - in real usage you'd want to pass a real callback
        typer.echo(f"Called {cmd_info.name} with {args} {kwargs}")
        return 0  # Return success code

    callback.__signature__ = inspect.Signature(params)  # type: ignore
    callback.__name__ = cmd_info.name
    callback.__doc__ = cmd_info.description

    return callback


def create_app(
    cmd_info: CommandInfo,
    callback: Callable[..., Any] | None = None,
) -> typer.Typer:
    """Create a Typer app from a CommandInfo object.

    Args:
        cmd_info: The CommandInfo object to convert
        callback: Optional callback function for the main command

    Returns:
        A Typer application with all commands and subcommands
    """
    app = typer.Typer(
        name=cmd_info.name,
        help=cmd_info.description,
        no_args_is_help=True,
    )

    if cmd_info.params:
        # If the main command has parameters, create a callback for it
        main_callback = callback or _create_callback(cmd_info, app)
        app.callback()(main_callback)

    # Add all subcommands recursively
    for subcmd in cmd_info.subcommands.values():
        if subcmd.subcommands:
            # It's a group - create a sub-Typer
            subapp = create_app(subcmd)
            app.add_typer(subapp, name=subcmd.name)
        else:
            # It's a command - create a callback
            cmd_callback = _create_callback(subcmd, app)
            app.command(
                name=subcmd.name,
                help=subcmd.description,
                hidden=subcmd.hidden,
            )(cmd_callback)

    return app


if __name__ == "__main__":
    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param

    # Example usage
    info = CommandInfo(
        name="mycli",
        description="A sample CLI",
        params=[
            Param(
                name="verbose",
                help="Increase verbosity",
                is_flag=True,
                opts=["-v", "--verbose"],
            )
        ],
        subcommands={
            "hello": CommandInfo(
                name="hello",
                description="Say hello",
                params=[
                    Param(
                        name="name",
                        help="Name to greet",
                        required=True,
                    ),
                    Param(
                        name="count",
                        help="Number of greetings",
                        opts=["--count", "-c"],
                        default=1,
                    ),
                ],
            )
        },
    )

    app = create_app(info)
    if __name__ == "__main__":
        app()
