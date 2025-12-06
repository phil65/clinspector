"""Module for generating Cappa CLI implementations from CommandInfo objects."""

from __future__ import annotations

import dataclasses
import typing
from typing import TYPE_CHECKING, Any

import cappa


if TYPE_CHECKING:
    from dataclasses import _MISSING_TYPE

    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


def _create_param_field(
    param: Param,
) -> tuple[str, type[str | list[str] | bool], dataclasses.Field[Any]]:
    """Create a dataclass field for a parameter."""
    type_hint: type[str | list[str] | bool] = str  # Default type
    if param.multiple:
        type_hint = list[str]
    elif param.is_flag:
        type_hint = bool

    # Create the Cappa Arg
    arg_kwargs: dict[str, Any] = {
        "help": param.help,
        "required": param.required,
        "hidden": param.hidden,
    }

    if param.opts:
        # Get short and long options
        short = None
        long = None
        for opt in param.opts:
            if opt.startswith("--"):
                long = opt.lstrip("-")
            elif opt.startswith("-"):
                short = opt.lstrip("-")
        arg_kwargs.update({"short": short, "long": long})

    arg = cappa.Arg[Any](**arg_kwargs)
    # Create the field with proper metadata typing
    default_value: Any | _MISSING_TYPE = (
        param.default if param.default is not None else dataclasses.MISSING
    )
    field: dataclasses.Field[Any] = dataclasses.field(default=default_value, metadata={0: arg})  # type: ignore
    return param.name, type_hint, field


def create_class(cmd_info: CommandInfo) -> type[Any]:
    """Create a Cappa dataclass from a CommandInfo object.

    Args:
        cmd_info: The CommandInfo object to convert

    Returns:
        A dataclass decorated with cappa.command
    """
    # Sort parameters - required ones first
    sorted_params = sorted(cmd_info.params, key=lambda p: (p.default is not None, p.name))

    # Create the callback first
    def dummy_callback(**kwargs: Any) -> None:
        """Placeholder callback."""
        print(f"Called {cmd_info.name} with: {kwargs}")

    # Create class with cappa's command decorator
    @cappa.command(name=cmd_info.name, help=cmd_info.description, invoke=dummy_callback)
    class DynamicCommand:
        """Dynamic command class."""

        for param in sorted_params:
            if param.opts:  # It's an option
                opt_type: type[str | list[str] | bool]
                if param.multiple:
                    opt_type = list[str]
                elif param.is_flag:
                    opt_type = bool
                else:
                    opt_type = str
                # Get short and long options
                short = None
                long = None
                for opt in param.opts:
                    if opt.startswith("--"):
                        long = opt.lstrip("-")
                    elif opt.startswith("-"):
                        short = opt.lstrip("-")

                locals()[param.name] = typing.Annotated[
                    opt_type,
                    cappa.Arg(
                        help=param.help,
                        short=short,
                        long=long,
                        required=param.required,
                        default=param.default,
                    ),
                ]
            else:  # It's a positional argument
                arg_type: type[str | list[str]]
                arg_type = list[str] if param.multiple else str
                arg = cappa.Arg(
                    help=param.help,
                    required=param.required,
                    default=param.default,
                )
                locals()[param.name] = typing.Annotated[arg_type, arg]

    return DynamicCommand


if __name__ == "__main__":
    import sys

    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param

    # Example usage
    params = [
        Param(name="name", help="Name to greet", required=True),
        Param(name="count", help="Number of greetings", opts=["--count", "-c"], default=1),
        Param(name="excited", help="Add exclamation marks", is_flag=True, opts=["--excited", "-e"]),
    ]
    info = CommandInfo(name="greet", description="A greeting command", params=params)
    GreetCommand = create_class(info)

    sys.exit(GreetCommand())  # cappa adds __call__ to run the command


# if __name__ == "__main__":
#     import sys

#     from clinspector.models.commandinfo import CommandInfo
#     from clinspector.models.param import Param

#     # Example usage
#     info = CommandInfo(
#         name="greet",
#         description="A greeting command",
#         params=[
#             Param(name="name", help="Name to greet", required=True),
#             Param(name="count", help="Number of greetings", opts=["--count", "-c"], default=1),
#             Param(
#                 name="excited",
#                 help="Add exclamation marks",
#                 is_flag=True,
#                 opts=["--excited", "-e"],
#             ),
#         ],
#     )

#     GreetCommand = create_class(info)
#     GreetCommand.run(sys.argv[1:])
