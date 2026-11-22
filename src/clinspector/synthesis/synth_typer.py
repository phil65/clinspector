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
    from clinspector.synthesis import Handler


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


def _create_callback(cmd_info: CommandInfo, handler: Handler | None) -> Callable[..., Any]:
    """Create a callback function with a signature matching the command's params."""
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

    def callback(**kwargs: Any) -> Any:
        return handler(cmd_info, kwargs) if handler else None

    callback.__signature__ = inspect.Signature(params)  # ty: ignore[missing-attribute]
    callback.__name__ = cmd_info.name.replace("-", "_") or "main"
    callback.__doc__ = cmd_info.description
    return callback


def create_app(cmd_info: CommandInfo, handler: Handler | None = None) -> typer.Typer:
    """Create a Typer app from a CommandInfo object.

    Args:
        cmd_info: The CommandInfo object to convert
        handler: Called with the invoked (sub)command's info and its parsed values.
                 The root command is invoked before subcommands, as usual for typer.

    Returns:
        A Typer application with all commands and subcommands
    """
    app = typer.Typer(
        name=cmd_info.name,
        help=cmd_info.description,
        no_args_is_help=True,
    )

    if handler or any(not is_help_param(p) for p in cmd_info.params):
        app.callback()(_create_callback(cmd_info, handler))

    # Add all subcommands recursively
    for name, subcmd in cmd_info.subcommands.items():
        if subcmd.subcommands:
            app.add_typer(create_app(subcmd, handler), name=name, hidden=subcmd.hidden)
        else:
            app.command(
                name=name,
                help=subcmd.description,
                hidden=subcmd.hidden,
                deprecated=subcmd.deprecated,
                epilog=subcmd.epilog,
            )(_create_callback(subcmd, handler))

    return app
