"""Introspection module for cyclopts CLI applications."""

from __future__ import annotations

import inspect
from typing import Any, Literal

from clinspector.models import commandinfo, param


def _extract_params_from_app(app: Any) -> list[param.Param]:
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
            if hasattr(parameter, "negative_bool") and parameter.negative_bool:
                opts.extend(f"--{name}" for name in parameter.negative_bool)

            # Check if it's a positional argument or option
            is_positional = not opts and not getattr(parameter, "option_name", None)

            # Build option names if not positional
            if not is_positional:
                option_name = getattr(parameter, "option_name", None)
                if option_name:
                    if len(option_name) == 1:
                        opts.append(f"-{option_name}")
                    else:
                        opts.append(f"--{option_name}")
                else:
                    # Derive from field name
                    field_name = field_info.name.replace("_", "-")
                    opts.append(f"--{field_name}")

            # Determine parameter type
            param_type_name: Literal["option", "parameter", "argument"] = (
                "argument" if is_positional else "option"
            )

            # Check if it's a flag (boolean with no value)
            is_flag = False
            if hasattr(field_info, "annotation"):
                # Simple check for boolean type
                annotation_str = str(field_info.annotation)
                is_flag = "bool" in annotation_str.lower()

            params.append(
                param.Param(
                    name=field_info.name,
                    help=getattr(parameter, "help", None)
                    or getattr(field_info, "description", None),
                    default=getattr(field_info, "default", None),
                    required=getattr(parameter, "required", False),
                    opts=opts,
                    is_flag=is_flag,
                    param_type_name=param_type_name,
                    multiple=getattr(parameter, "multiple", False),
                    hidden=not getattr(parameter, "show", True),
                    metavar=getattr(parameter, "metavar", None),
                    envvar=getattr(parameter, "env_var", None),
                )
            )

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

                params.append(
                    param.Param(
                        name=param_name,
                        default=default_val,
                        required=required,
                        param_type_name="argument",
                    )
                )
        except (AttributeError, TypeError, ValueError):
            params = []

    return params


def _parse_app(app: Any, parent_name: str = "") -> commandinfo.CommandInfo:
    """Parse a cyclopts App into a CommandInfo object.

    Args:
        app: Cyclopts App instance
        parent_name: Name of parent command for building full paths

    Returns:
        CommandInfo object
    """
    # Get app name - cyclopts apps can have multiple names via tuples
    app_names = app.name if hasattr(app, "name") else ()
    if not app_names:
        name = ""
    elif isinstance(app_names, (list, tuple)):
        name = app_names[0] if app_names else ""
    else:
        name = str(app_names)

    # Build full name including parent
    full_name = f"{parent_name} {name}".strip() if parent_name else name

    # Get description from help property
    description = ""
    if hasattr(app, "help") and app.help:
        description = app.help

    # Get usage string
    usage = app.usage if hasattr(app, "usage") and app.usage else full_name

    # Extract parameters from default command
    params = _extract_params_from_app(app)

    # Parse subcommands
    subcommands = {}
    if hasattr(app, "_commands"):
        for cmd_name, sub_app in app._commands.items():
            # Skip help and version commands
            if (hasattr(app, "help_flags") and cmd_name in app.help_flags) or (
                hasattr(app, "version_flags") and cmd_name in app.version_flags
            ):
                continue

            try:
                sub_info = _parse_app(sub_app, full_name)
                subcommands[cmd_name] = sub_info
            except (AttributeError, TypeError, ValueError):
                # Create minimal command info for problematic subcommands
                subcommands[cmd_name] = commandinfo.CommandInfo(
                    name=cmd_name,
                    description="",
                )

    # Check if hidden
    hidden = not getattr(app, "show", True)

    # Get epilog
    epilog = getattr(app, "epilog", None)

    # Get callback
    callback = getattr(app, "default_command", None)

    return commandinfo.CommandInfo(
        name=name,
        description=description,
        usage=usage,
        params=params,
        subcommands=subcommands,
        hidden=hidden,
        epilog=epilog,
        callback=callback,
    )


def get_info(
    instance: Any,
    command: str | None = None,
) -> commandinfo.CommandInfo:
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
                return commandinfo.CommandInfo(
                    name=cmd,
                    description=f"Command '{cmd}' not found",
                )

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
