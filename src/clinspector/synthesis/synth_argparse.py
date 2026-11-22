"""Module for generating ArgumentParser CLI implementations from CommandInfo objects."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

from clinspector.synthesis import is_help_param


if TYPE_CHECKING:
    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


def _add_param(parser: argparse.ArgumentParser, param: Param) -> None:
    """Add a parameter to an ArgumentParser instance.

    Args:
        parser: The parser to add the parameter to
        param: The parameter to add
    """
    if is_help_param(param):
        return
    kwargs: dict[str, Any] = {
        "help": argparse.SUPPRESS if param.hidden else param.help,
        "default": param.default,
    }
    if param.choices:
        kwargs["choices"] = param.choices
    if param.metavar:
        kwargs["metavar"] = param.metavar

    if param.opts:  # It's an optional argument
        kwargs["dest"] = param.name
        if param.count:
            kwargs["action"] = "count"
            kwargs.pop("metavar", None)
        elif param.is_flag:
            kwargs["action"] = (
                argparse.BooleanOptionalAction if param.secondary_opts else "store_true"
            )
            kwargs.pop("metavar", None)
            kwargs.pop("choices", None)
            if param.default is None:
                kwargs["default"] = False
        elif param.multiple:
            kwargs["action"] = "append"
        if param.required:
            kwargs["required"] = True
        parser.add_argument(*param.opts, **kwargs)
    else:  # It's a positional argument
        if param.multiple or param.nargs == -1:
            kwargs["nargs"] = "+" if param.required else "*"
        elif not param.required:
            kwargs["nargs"] = "?"
        elif isinstance(param.nargs, int | str) and param.nargs not in (1, None):
            kwargs["nargs"] = param.nargs
        parser.add_argument(param.name, **kwargs)


def _populate(parser: argparse.ArgumentParser, cmd_info: CommandInfo, depth: int = 0) -> None:
    for param in cmd_info.params:
        _add_param(parser, param)
    if not cmd_info.subcommands:
        return
    dest = "command" if depth == 0 else f"{cmd_info.name}_command"
    subparsers = parser.add_subparsers(title="commands", dest=dest, required=True)
    for name, subcmd in cmd_info.subcommands.items():
        subparser = subparsers.add_parser(
            name,
            help=argparse.SUPPRESS if subcmd.hidden else subcmd.description,
            description=subcmd.description,
            epilog=subcmd.epilog,
        )
        _populate(subparser, subcmd, depth + 1)


def create_parser(cmd_info: CommandInfo) -> argparse.ArgumentParser:
    """Create an ArgumentParser from a CommandInfo object.

    Args:
        cmd_info: The CommandInfo object to convert

    Returns:
        An ArgumentParser with all commands and (nested) subcommands
    """
    parser = argparse.ArgumentParser(
        prog=cmd_info.name,
        description=cmd_info.description,
        epilog=cmd_info.epilog,
    )
    _populate(parser, cmd_info)
    return parser
