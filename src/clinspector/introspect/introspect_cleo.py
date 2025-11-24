"""Module for inspecting Cleo CLI applications."""

from __future__ import annotations

from cleo.application import Application
from cleo.commands.command import Command

from clinspector.models import commandinfo, param


def _parse_command(command: Command) -> commandinfo.CommandInfo:
    """Parse a Cleo Command into a CommandInfo object."""
    # Get definition object which contains argument/option configurations
    definition = command.definition
    # Parse arguments
    params = [
        param.Param(
            name=argument.name,
            help=argument.description,
            default=argument.default,
            required=argument._required,
            param_type_name="argument",
            multiple=argument._is_list,
        )
        for argument in definition.arguments
    ] + [
        param.Param(
            name=option.name,
            help=option.description,
            default=option.default,
            opts=[f"--{option.name}"] + ([f"-{option.shortcut}"] if option.shortcut else []),
            # required=option.required,
            is_flag=option._flag,
            multiple=option._is_list,
            param_type_name="option",
        )
        for option in definition.options
    ]

    return commandinfo.CommandInfo(
        name=command.name or "",
        description=command.description,
        # usage=command._synopsis,
        params=params,
        hidden=command.hidden,
        callback=command.handle,
    )


def parse(app: Application) -> commandinfo.CommandInfo:
    """Parse a Cleo Application into a CommandInfo object."""
    # Get the default command (usually "list")
    default_cmd_name = app._default_command
    default_cmd = app._commands[default_cmd_name]  # Get actual command object

    # Build subcommands dict
    subcommands = {
        name: _parse_command(cmd) for name, cmd in app._commands.items() if name != default_cmd_name
    }

    return commandinfo.CommandInfo(
        name=app.name or "",
        description=app.long_version or "",
        # usage=app.definition,  # TODO
        subcommands=subcommands,
        params=_parse_command(default_cmd).params,
    )


def get_info(
    instance: Application,
    command: str | None = None,
) -> commandinfo.CommandInfo:
    """Return a CommandInfo object for command of given Cleo Application.

    Args:
        instance: A Cleo Application instance
        command: The command to get info for
    """
    info = parse(instance)
    if command:
        return info.subcommands.get(command, info)
    return info


if __name__ == "__main__":
    import typing

    from cleo.helpers import argument, option

    # Example usage with a simple Cleo application
    class GreetCommand(Command):
        name = "greet"
        description = "Greets someone"
        arguments: typing.ClassVar = [
            argument("name", description="Who do you want to greet?", optional=True)
        ]
        options: typing.ClassVar = [
            option(
                "yell",
                "y",
                description="If set, the task will yell in uppercase letters",
                flag=True,
            )
        ]

        def handle(self):
            name = self.argument("name")
            text = f"Hello {name}" if name else "Hello"
            if self.option("yell"):
                text = text.upper()
            self.line(text)

    app = Application()
    app.add(GreetCommand())

    info = get_info(app)
    print(info)
