"""Module for generating Cleo CLI implementations from CommandInfo objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from cleo.application import Application
from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument


if TYPE_CHECKING:
    from cleo.io.inputs.option import Option

    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


def _param_to_config(param: Param) -> tuple[Argument | Option, dict[str, str]]:
    """Convert a Param to Cleo argument/option configuration."""
    if param.opts:  # It's an option
        long_name = None
        short_name = None
        for opt in param.opts:
            if opt.startswith("--"):
                long_name = opt.lstrip("-")
            elif opt.startswith("-"):
                short_name = opt.lstrip("-")

        if not long_name:
            long_name = param.name

        return (
            option(
                long_name=long_name,
                short_name=short_name,
                description=param.help,
                flag=param.is_flag,
                value_required=not param.is_flag,
                multiple=param.multiple,
                default=param.default,
            ),
            {"option": long_name},
        )

    # It's an argument
    return (
        argument(
            name=param.name,
            description=param.help,
            optional=not param.required,
            multiple=param.multiple,
            default=param.default,
        ),
        {"argument": param.name},
    )


def _create_command_class(cmd_info: CommandInfo) -> type[Command]:
    """Create a Cleo Command class from a CommandInfo object."""
    arguments: list[Argument] = []
    options: list[Option] = []
    param_getters: dict[str, dict[str, str]] = {}

    for param in cmd_info.params:
        config, getter = _param_to_config(param)
        param_getters[param.name] = getter
        if isinstance(config, Argument):
            arguments.append(config)
        else:
            options.append(config)

    # Create the command class
    class DynamicCommand(Command):
        name = cmd_info.name
        description = cmd_info.description or ""
        hidden = cmd_info.hidden

        arguments_: ClassVar = arguments
        options_: ClassVar = options

        def handle(self) -> int:
            """Execute the command."""
            values = {}
            for name, getter in param_getters.items():
                if "argument" in getter:
                    values[name] = self.argument(getter["argument"])
                else:
                    values[name] = self.option(getter["option"])

            # This is where you'd handle the actual command execution
            self.line(f"Command {self.name} called with values: {values}")
            return 0

    return DynamicCommand


def create_app(cmd_info: CommandInfo) -> Application:
    """Create a Cleo Application from a CommandInfo object.

    Args:
        cmd_info: The CommandInfo object to convert

    Returns:
        A Cleo Application with all commands and subcommands
    """
    app = Application(name=cmd_info.name, version="1.0.0")

    # Create default command if main command has parameters
    if cmd_info.params:
        app.add(_create_command_class(cmd_info)())

    # Add all subcommands recursively
    def add_commands(commands: dict[str, CommandInfo]) -> None:
        for subcmd in commands.values():
            cmd_class = _create_command_class(subcmd)
            app.add(cmd_class())
            if subcmd.subcommands:
                add_commands(subcmd.subcommands)

    add_commands(cmd_info.subcommands)

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
    app.run()
