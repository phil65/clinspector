from __future__ import annotations

import argparse

from clinspector.models import commandinfo, param


def parse(parser: argparse.ArgumentParser) -> commandinfo.CommandInfo:
    """Recursively parse an ArgumentParser instance and return a `CommandInfo` object."""
    try:
        subparse_action = next(
            i for i in parser._actions if isinstance(i, argparse._SubParsersAction)
        )
        subcommands = {i: parse(j) for i, j in subparse_action.choices.items()}
    except StopIteration:
        subcommands = {}
    params = [
        param.Param(
            metavar=" ".join(i.metavar) if isinstance(i.metavar, tuple) else i.metavar,
            help=i.help,
            default=i.default if i.default != argparse.SUPPRESS else None,
            opts=list(i.option_strings),
            nargs=i.nargs,
            required=i.required,
            # dest: str
            # const: Any
            # choices: Iterable[Any] | None
        )
        for i in parser._actions
    ]
    return commandinfo.CommandInfo(
        name=parser.prog,
        description=parser.description or "",
        usage=parser.format_usage(),
        params=params,
        subcommands=subcommands,
    )


def get_info(
    instance: argparse.ArgumentParser,
    command: str | None = None,
) -> commandinfo.CommandInfo:
    """Return a `CommmandInfo` object for command of given instance.

    Args:
        instance: A `ArgumentParser` instance
        command: The command to get info for. (also accepts dot notation for subcommands)
    """
    info = parse(instance)
    if command:
        for cmd in command.split("."):
            info = info[cmd]
    return info
