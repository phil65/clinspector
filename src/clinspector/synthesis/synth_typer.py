"""Module for generating Typer CLI implementations from CommandInfo objects."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Literal

import typer

from clinspector.synthesis import is_help_param


if TYPE_CHECKING:
    from collections.abc import Callable

    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


def _annotation(param: Param) -> Any:
    """Return a type annotation matching the given param."""
    if param.count:
        return int
    if param.is_flag:
        return bool
    base: Any = Literal[tuple(param.choices)] if param.choices else str  # ty: ignore[invalid-type-form]
    return list[base] if param.multiple or param.nargs == -1 else base


def _typer_param(param: Param) -> Any:
    """Return a `typer.Option` / `typer.Argument` for the given param."""
    default = ... if param.required else param.default
    if param.opts:
        decls = list(param.opts)
        if param.secondary_opts:
            decls = [f"{decls[0]}/{param.secondary_opts[0]}", *decls[1:]]
        if param.count and default is None:
            default = 0
        if param.is_flag and not param.count and default is None:
            default = False
        return typer.Option(
            default,
            *decls,
            help=param.help,
            hidden=param.hidden,
            envvar=param.envvar,
            metavar=param.metavar,
            count=param.count,
        )
    return typer.Argument(default, help=param.help, hidden=param.hidden, metavar=param.metavar)


def _create_callback(
    cmd_info: CommandInfo,
    callback: Callable[..., Any] | None = None,
) -> Callable[..., Any]:
    """Create a callback function with a signature matching the command's params.

    Args:
        cmd_info: The command to create a callback for
        callback: Function receiving the parsed values as keyword arguments.
                  If not given, a placeholder echoing the values is used.
    """
    params = [
        inspect.Parameter(
            name=p.name,
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=_typer_param(p),
            annotation=_annotation(p),
        )
        for p in cmd_info.params
        if not is_help_param(p)
    ]

    def wrapper(**kwargs: Any) -> Any:
        if callback is not None:
            return callback(**kwargs)
        typer.echo(f"Called {cmd_info.name} with {kwargs}")
        return None

    wrapper.__signature__ = inspect.Signature(params)  # ty: ignore[missing-attribute]
    wrapper.__name__ = cmd_info.name.replace("-", "_") or "main"
    wrapper.__doc__ = cmd_info.description
    return wrapper


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

    if callback or any(not is_help_param(p) for p in cmd_info.params):
        # If the main command has parameters, create a callback for it
        app.callback()(_create_callback(cmd_info, callback))

    # Add all subcommands recursively
    for name, subcmd in cmd_info.subcommands.items():
        if subcmd.subcommands:
            app.add_typer(create_app(subcmd), name=name, hidden=subcmd.hidden)
        else:
            app.command(
                name=name,
                help=subcmd.description,
                hidden=subcmd.hidden,
                deprecated=subcmd.deprecated,
                epilog=subcmd.epilog,
            )(_create_callback(subcmd))

    return app
