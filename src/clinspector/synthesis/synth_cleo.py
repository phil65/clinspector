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


_APP_OPTIONS = {"help", "quiet", "verbose", "version", "ansi", "no-ansi", "no-interaction"}


def _param_to_config(param: Param) -> tuple[Argument | Option, dict[str, str]]:
    """Convert a Param to Cleo argument/option configuration."""
    if param.opts:  # It's an option
        long_name = next((o[2:] for o in param.opts if o.startswith("--")), param.name)
        shorts = [o[1:] for o in param.opts if o.startswith("-") and not o.startswith("--")]
        is_flag = param.is_flag or param.count
        default = None if is_flag else param.default
        if param.multiple and default is not None:
            default = list(default) if isinstance(default, list | tuple) else [default]
        return (
            option(
                long_name=long_name,
                short_name="|".join(shorts) or None,
                description=param.help,
                flag=is_flag,
                value_required=not is_flag,
                multiple=param.multiple,
                default=default,
            ),
            {"option": long_name},
        )

    # It's an argument
    default = None if param.required else param.default
    if param.multiple and default is not None:
        default = list(default) if isinstance(default, list | tuple) else [default]
    return (
        argument(
            name=param.name,
            description=param.help,
            optional=not param.required,
            multiple=param.multiple,
            default=default,
        ),
        {"argument": param.name},
    )


def _create_command_class(cmd_info: CommandInfo, name: str | None = None) -> type[Command]:
    """Create a Cleo Command class from a CommandInfo object."""
    args: list[Argument] = []
    opts: list[Option] = []
    param_getters: dict[str, dict[str, str]] = {}

    for param in cmd_info.params:
        if param.opts and param.name in _APP_OPTIONS:
            continue  # added by the cleo Application itself
        config, getter = _param_to_config(param)
        param_getters[param.name] = getter
        if isinstance(config, Argument):
            args.append(config)
        else:
            opts.append(config)

    # Create the command class
    class DynamicCommand(Command):
        arguments: ClassVar[list[Argument]] = args  # type: ignore[misc]
        options: ClassVar[list[Option]] = opts  # type: ignore[misc]

        def handle(self) -> int:
            """Execute the command."""
            values = {}
            for param_name, getter in param_getters.items():
                if "argument" in getter:
                    values[param_name] = self.argument(getter["argument"])
                else:
                    values[param_name] = self.option(getter["option"])

            # This is where you'd handle the actual command execution
            self.line(f"Command {self.name} called with values: {values}")
            return 0

    DynamicCommand.name = name or cmd_info.name
    DynamicCommand.description = cmd_info.description or ""
    DynamicCommand.hidden = cmd_info.hidden
    return DynamicCommand


def create_app(cmd_info: CommandInfo) -> Application:
    """Create a Cleo Application from a CommandInfo object.

    Nested subcommands are registered with space-separated names (`"group sub"`).

    Args:
        cmd_info: The CommandInfo object to convert

    Returns:
        A Cleo Application with all commands and subcommands
    """
    app = Application(name=cmd_info.name, version="1.0.0")

    # Create default command if main command has parameters
    if any(p.name not in _APP_OPTIONS for p in cmd_info.params):
        app.add(_create_command_class(cmd_info)())

    # Add all subcommands recursively
    def add_commands(commands: dict[str, CommandInfo], prefix: str = "") -> None:
        for name, subcmd in commands.items():
            full_name = f"{prefix}{name}"
            app.add(_create_command_class(subcmd, name=full_name)())
            if subcmd.subcommands:
                add_commands(subcmd.subcommands, prefix=f"{full_name} ")

    add_commands(cmd_info.subcommands)
    return app
