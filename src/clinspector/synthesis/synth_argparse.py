"""Module for generating ArgumentParser CLI implementations from CommandInfo objects."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


def _add_param(parser: argparse.ArgumentParser, param: Param):
    """Add a parameter to an ArgumentParser instance.

    Args:
        parser: The parser to add the parameter to
        param: The parameter to add
    """
    kwargs = {
        "help": param.help,
        "default": param.default,
    }

    if param.multiple:
        kwargs["nargs"] = "*"
    if param.metavar:
        kwargs["metavar"] = param.metavar
    if param.is_flag:
        kwargs["action"] = "store_true"

    if param.opts:  # It's an optional argument
        kwargs["required"] = param.required
        parser.add_argument(*param.opts, **kwargs)
    else:  # It's a positional argument
        # Don't include 'required' for positional arguments
        # If it's optional, use nargs='?' if not already set
        if not param.required and "nargs" not in kwargs:
            kwargs["nargs"] = "?"
        parser.add_argument(param.name, **kwargs)


def create_parser(cmd_info: CommandInfo) -> argparse.ArgumentParser:
    """Create an ArgumentParser from a CommandInfo object.

    Args:
        cmd_info: The CommandInfo object to convert

    Returns:
        An ArgumentParser with all commands and subcommands
    """
    parser = argparse.ArgumentParser(
        prog=cmd_info.name,
        description=cmd_info.description,
        epilog=cmd_info.epilog,
    )

    # Add all parameters
    for param in cmd_info.params:
        _add_param(parser, param)

    # Add subcommands if any
    if cmd_info.subcommands:
        subparsers = parser.add_subparsers(
            title="commands",
            dest="command",
            required=bool(cmd_info.subcommands),  # Required if there are subcommands
        )
        for name, subcmd in cmd_info.subcommands.items():
            subparser = subparsers.add_parser(
                name,
                help=subcmd.description,
                description=subcmd.description,
                epilog=subcmd.epilog,
            )
            # Recursively add parameters and subcommands
            for param in subcmd.params:
                _add_param(subparser, param)
            if subcmd.subcommands:
                # Recursive call for nested subcommands
                sub_subparsers = subparser.add_subparsers(
                    title="commands",
                    dest=f"{name}_command",
                    required=bool(subcmd.subcommands),
                )
                for sub_name, sub_subcmd in subcmd.subcommands.items():
                    sub_subparser = sub_subparsers.add_parser(
                        sub_name,
                        help=sub_subcmd.description,
                        description=sub_subcmd.description,
                        epilog=sub_subcmd.epilog,
                    )
                    for param in sub_subcmd.params:
                        _add_param(sub_subparser, param)

    return parser


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

    parser = create_parser(info)

    # Test with sample arguments
    import sys

    test_args = ["hello", "world", "--count", "3"]  # Sample command
    args = parser.parse_args(test_args if len(sys.argv) == 1 else sys.argv[1:])
    print(f"Parsed arguments: {args}")
