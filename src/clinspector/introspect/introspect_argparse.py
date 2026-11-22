from __future__ import annotations

import argparse
from typing import Any

from clinspector.introspect._utils import resolve_command
from clinspector.models import commandinfo, param


_FLAG_ACTIONS = (
    argparse._StoreTrueAction,
    argparse._StoreFalseAction,
    argparse._StoreConstAction,
    argparse._AppendConstAction,
    argparse._CountAction,
    argparse._HelpAction,
    argparse._VersionAction,
    argparse.BooleanOptionalAction,
)
_MULTIPLE_ACTIONS = (argparse._AppendAction, argparse._AppendConstAction, argparse._ExtendAction)


def _parse_action(action: argparse.Action) -> param.Param:
    """Convert an argparse `Action` into a `Param`."""
    opts = list(action.option_strings)
    secondary_opts: list[str] = []
    if isinstance(action, argparse.BooleanOptionalAction):
        secondary_opts = [o for o in opts if o.startswith("--no-")]
        opts = [o for o in opts if o not in secondary_opts]
    hidden = action.help == argparse.SUPPRESS
    type_name = getattr(action.type, "__name__", None)
    return param.Param(
        name=action.dest,
        param_type_name="option" if action.option_strings else "argument",
        metavar=" ".join(action.metavar) if isinstance(action.metavar, tuple) else action.metavar,
        help=None if hidden else action.help,
        hidden=hidden,
        default=None if action.default == argparse.SUPPRESS else action.default,
        opts=opts,
        secondary_opts=secondary_opts,
        nargs=1 if action.nargs is None else action.nargs,
        required=action.required,
        is_flag=isinstance(action, _FLAG_ACTIONS),
        count=isinstance(action, argparse._CountAction),
        multiple=isinstance(action, _MULTIPLE_ACTIONS),
        choices=[str(c) for c in action.choices] if action.choices is not None else None,
        type={"name": type_name} if type_name and type_name != "<lambda>" else None,
    )


def _usage(parser: argparse.ArgumentParser) -> str:
    return parser.format_usage().strip().removeprefix("usage: ")


def parse(
    parser: argparse.ArgumentParser,
    name: str | None = None,
    help_text: str | None = None,
    deprecated: bool = False,
) -> commandinfo.CommandInfo:
    """Recursively parse an ArgumentParser instance and return a `CommandInfo` object.

    Args:
        parser: The parser to inspect.
        name: The command name (defaults to the parser's `prog`).
        help_text: Help text used if the parser has no description (subparser help).
        deprecated: Whether the command is marked as deprecated.
    """
    subcommands: dict[str, commandinfo.CommandInfo] = {}
    params: list[param.Param] = []
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            params.append(_parse_action(action))
            continue
        helps = {a.dest: a.help for a in action._choices_actions}
        deprecated_names = getattr(action, "_deprecated", set())
        seen: set[int] = set()
        for sub_name, subparser in action.choices.items():
            if id(subparser) in seen:  # aliases point to the same parser
                continue
            seen.add(id(subparser))
            subcommands[sub_name] = parse(
                subparser,
                name=sub_name,
                help_text=helps.get(sub_name),
                deprecated=sub_name in deprecated_names,
            )
    func: Any = parser.get_default("func")
    return commandinfo.CommandInfo(
        name=name or parser.prog,
        description=parser.description or help_text or "",
        usage=_usage(parser),
        params=params,
        subcommands=subcommands,
        epilog=parser.epilog,
        deprecated=deprecated,
        callback=func if callable(func) else None,
    )


def get_info(
    instance: argparse.ArgumentParser,
    command: str | None = None,
) -> commandinfo.CommandInfo:
    """Return a `CommandInfo` object for command of given instance.

    Args:
        instance: A `ArgumentParser` instance
        command: The command to get info for. (also accepts dot notation for subcommands)
    """
    return resolve_command(parse(instance), command)
