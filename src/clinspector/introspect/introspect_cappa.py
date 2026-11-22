"""Introspection module for cappa CLI applications."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import cappa
from cappa.arg import ArgAction
from cappa.default import Env
from cappa.type_view import Empty

from clinspector.introspect._utils import annotation_type_name, resolve_command
from clinspector.models import commandinfo, param


if TYPE_CHECKING:
    from cappa.arg import Arg
    from cappa.command import Command


_FLAG_ACTIONS = {
    ArgAction.store_true,
    ArgAction.store_false,
    ArgAction.count,
    ArgAction.help,
    ArgAction.version,
}
_MULTIPLE_ACTIONS = {ArgAction.append}


def _default_and_env(arg: Arg[Any]) -> tuple[Any, str | None]:
    default = arg.default
    if default is None or default is Empty:
        return None, None
    value = getattr(default, "default", default)
    envvar = next(
        (d.env_vars[0] for d in getattr(default, "sequence", ()) if isinstance(d, Env)),
        None,
    )
    return (None if value is Empty else value), envvar


def _flags(value: Any) -> list[str]:
    """Normalize a collected cappa `short` / `long` value (False or list) to a list."""
    if isinstance(value, str):
        return [value]
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _get_param_from_arg(arg: Arg[Any]) -> param.Param:
    """Convert a (collected) cappa `Arg` to a Param object."""
    opts = [*_flags(arg.short), *_flags(arg.long)]
    default, envvar = _default_and_env(arg)
    action = arg.action
    num_args = arg.num_args if isinstance(arg.num_args, int) else 1
    field_name = str(arg.field_name)
    metavar = arg.value_name if isinstance(arg.value_name, str) else None
    return param.Param(
        name=field_name,
        help=arg.help or None,
        default=default,
        envvar=envvar,
        required=bool(arg.required),
        opts=opts,
        is_flag=action in _FLAG_ACTIONS,
        count=action is ArgAction.count,
        multiple=action in _MULTIPLE_ACTIONS or num_args == -1,
        nargs=num_args,
        choices=[str(c) for c in arg.choices] if arg.choices else None,
        type=annotation_type_name(getattr(arg.type_view, "annotation", None)),
        metavar=metavar if metavar != field_name else None,
        hidden=bool(arg.hidden),
        param_type_name="option" if opts else "argument",
    )


def _usage(name: str, params: list[param.Param], has_subcommands: bool) -> str:
    parts = [name]
    if any(p.opts for p in params):
        parts.append("[OPTIONS]")
    parts.extend(p.name.upper() for p in params if not p.opts)
    if has_subcommands:
        parts.append("COMMAND")
    return " ".join(parts)


def _parse_command(command: Command[Any]) -> commandinfo.CommandInfo:
    params: list[param.Param] = []
    subcommands: dict[str, commandinfo.CommandInfo] = {}
    for arg in command.arguments:
        if isinstance(arg, cappa.Subcommand):
            for name, sub in (arg.options or {}).items():
                subcommands[name] = _parse_command(sub)
        elif isinstance(arg, cappa.Arg):
            params.append(_get_param_from_arg(arg))
    name = command.real_name()
    description = "\n\n".join(s for s in (command.help, command.description) if s)
    return commandinfo.CommandInfo(
        name=name,
        description=description,
        usage=_usage(name, params, bool(subcommands)),
        params=params,
        subcommands=subcommands,
        hidden=bool(command.hidden),
        deprecated=bool(command.deprecated),
        epilog=command.epilog if isinstance(command.epilog, str) else None,
        callback=command.invoke if callable(command.invoke) else None,
    )


def get_info(cls: type[Any], command: str | None = None) -> commandinfo.CommandInfo:
    """Extract CLI information from a cappa command class.

    Args:
        cls: The (dataclass-like) command class to analyze
        command: The command to get info for (supports dot notation for subcommands).
    """
    collected = cappa.collect(cls, help=False, completion=False)
    return resolve_command(_parse_command(collected), command)
