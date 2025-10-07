"""Introspection module for cyclopts CLI applications."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Literal

from clinspector.models import commandinfo, param


if TYPE_CHECKING:
    from cyclopts import App


ParamType = Literal["option", "parameter", "argument"]


def _extract_params_from_app(app: App) -> list[param.Param]:
    """Extract parameters from a cyclopts App's default command.

    Args:
        app: Cyclopts App instance

    Returns:
        List of Param objects
    """
    if not app.default_command:
        return []

    try:
        # Get the argument collection which contains parameter info
        argument_collection = app.assemble_argument_collection(parse_docstring=True)
        params = []

        for argument in argument_collection:
            field_info = argument.field_info
            parameter = argument.parameter

            # Extract option strings
            opts: list[str] = []
            # Handle negative boolean flags
            if parameter.negative_bool:
                opts.extend(f"--{name}" for name in parameter.negative_bool)

            # Check if it's a positional argument or option
            option_name = getattr(parameter, "option_name", None)
            is_positional = not opts and not option_name

            # Build option names if not positional
            if not is_positional:
                if name := option_name:
                    label = f"-{name}" if len(name) == 1 else f"--{name}"
                else:
                    # Derive from field name
                    label = "--" + field_info.name.replace("_", "-")
                opts.append(label)

            # Determine parameter type
            param_type_name: ParamType = "argument" if is_positional else "option"
            # Simple check for boolean type
            p = param.Param(
                name=field_info.name,
                help=parameter.help or getattr(field_info, "description", None),
                default=field_info.default,
                required=parameter.required or False,
                opts=opts,
                is_flag="bool" in str(field_info.annotation).lower(),
                param_type_name=param_type_name,
                multiple=getattr(parameter, "multiple", False),
                hidden=not parameter.show,
                metavar=getattr(parameter, "metavar", None),
                envvar=env_var
                if isinstance((env_var := parameter.env_var), str | None)
                else None,
            )
            params.append(p)

    except (AttributeError, TypeError, ValueError):
        # Fallback: try to inspect the function signature directly
        try:
            sig = inspect.signature(app.default_command)
            params = []
            for param_name, param_obj in sig.parameters.items():
                default_val = (
                    param_obj.default
                    if param_obj.default != inspect.Parameter.empty
                    else None
                )
                required = param_obj.default == inspect.Parameter.empty
                p = param.Param(
                    name=param_name,
                    default=default_val,
                    required=required,
                    param_type_name="argument",
                )
                params.append(p)
        except (AttributeError, TypeError, ValueError):
            params = []

    return params


def _parse_app(app: App, parent_name: str = "") -> commandinfo.CommandInfo:
    """Parse a cyclopts App into a CommandInfo object.

    Args:
        app: Cyclopts App instance
        parent_name: Name of parent command for building full paths

    Returns:
        CommandInfo object
    """
    # Get app name - cyclopts apps can have multiple names via tuples
    name = "" if not app.name else app.name[0] if app.name else ""
    # Build full name including parent
    full_name = f"{parent_name} {name}".strip() if parent_name else name
    usage = app.usage if app.usage else full_name  # Get usage string

    # Extract parameters from default command
    params = _extract_params_from_app(app)

    # Parse subcommands
    subcommands = {}
    for cmd_name, sub_app in app._commands.items():
        # Skip help and version commands
        if (cmd_name in app.help_flags) or (cmd_name in app.version_flags):
            continue
        try:
            sub_info = _parse_app(sub_app, full_name)
            subcommands[cmd_name] = sub_info
        except (AttributeError, TypeError, ValueError):
            # Create minimal command info for problematic subcommands
            subcommands[cmd_name] = commandinfo.CommandInfo(name=cmd_name)

    return commandinfo.CommandInfo(
        name=name,
        description=app.help,
        usage=usage,
        params=params,
        subcommands=subcommands,
        hidden=not app.show,
        epilog=getattr(app, "epilog", None),
        callback=app.default_command,
    )


def get_info(instance: Any, command: str | None = None) -> commandinfo.CommandInfo:
    """Return a CommandInfo object for command of given cyclopts App.

    Args:
        instance: A cyclopts App instance
        command: The command to get info for (supports dot notation for subcommands)

    Returns:
        CommandInfo object with extracted information
    """
    info = _parse_app(instance)

    if command:
        # Navigate to specific subcommand using dot notation
        for cmd in command.split("."):
            if cmd in info.subcommands:
                info = info.subcommands[cmd]
            else:
                # Command not found, return empty info
                desc = f"Command '{cmd}' not found"
                return commandinfo.CommandInfo(name=cmd, description=desc)

    return info


if __name__ == "__main__":
    # Example usage - would need cyclopts installed
    try:
        import cyclopts

        app = cyclopts.App(name="example", help="Example cyclopts application")

        @app.default
        def main(name: str = "World", count: int = 1, verbose: bool = False):
            """Main command that greets someone."""
            for _ in range(count):
                greeting = f"Hello, {name}!"
                if verbose:
                    print(f"Verbose: {greeting}")
                else:
                    print(greeting)

        @app.command
        def subcommand(arg: str, flag: bool = False):
            """A subcommand example."""
            print(f"Subcommand called with arg={arg}, flag={flag}")

        info = get_info(app)
        print(f"App: {info.name}")
        print(f"Description: {info.description}")
        print(f"Parameters: {len(info.params)}")
        print(f"Subcommands: {list(info.subcommands.keys())}")

    except ImportError:
        print("cyclopts not available for testing")
