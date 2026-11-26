"""Helpers shared by the framework introspection modules."""

from collections.abc import Sequence
import types
import typing
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from clinspector.models.commandinfo import CommandInfo


def resolve_command(info: CommandInfo, command: str | None) -> CommandInfo:
    """Return the subcommand of `info` addressed by `command`.

    `command` may be a subcommand name, a dotted path (`"group.sub"`) or a path that
    starts with the name of the root command (`"tool.group.sub"`). An exact key match
    (frameworks like cleo use names containing spaces) wins over path splitting.

    If no matching subcommand exists, the root `info` is returned.

    Args:
        info: The root command.
        command: The (dotted) name of the subcommand to look up.
    """
    if not command:
        return info
    if command in info.subcommands:
        return info[command]
    parts = command.split(".")
    if parts[0] == info.name and parts[0] not in info.subcommands:
        parts = parts[1:]
    current = info
    for part in parts:
        if part not in current.subcommands:
            return info
        current = current[part]
    return current


def first_envvar(envvar: Any) -> str | None:
    """Normalize an envvar setting (string, sequence or None) to a single name."""
    if isinstance(envvar, str):
        return envvar or None
    if isinstance(envvar, Sequence) and envvar and isinstance(envvar[0], str):
        return envvar[0]
    return None


_CLICK_TYPE_NAMES = {
    "text": "str",
    "integer": "int",
    "integer range": "int",
    "float range": "float",
    "boolean": "bool",
    "filename": "file",
}


def type_name(obj: Any) -> str | None:
    """Return a normalized type name for a Python type or a click `ParamType`.

    Python types map to their name (`int` -> `"int"`), click types to the matching
    Python-style name (`click.INT` -> `"int"`, `click.Path()` -> `"path"`).
    """
    if obj is None:
        return None
    if isinstance(obj, type):
        return obj.__name__
    if isinstance(name := getattr(obj, "name", None), str):  # click ParamType
        return _CLICK_TYPE_NAMES.get(name, name)
    name = getattr(obj, "__name__", None)  # callables like argparse `type=` functions
    return None if name in (None, "<lambda>") else name


def annotation_type_name(annotation: Any) -> str | None:
    """Return a type name for a Python type annotation.

    `Annotated`, optional (`X | None`) and container (`list[X]`, `tuple[X, ...]`)
    annotations are unwrapped to the item type, `Literal` maps to `"choice"`.
    """
    origin = typing.get_origin(annotation)
    args = [a for a in typing.get_args(annotation) if a is not type(None) and a is not Ellipsis]
    if origin is typing.Annotated:
        return annotation_type_name(args[0])
    if origin is typing.Literal:
        return "choice"
    if origin in (typing.Union, types.UnionType) and len(args) == 1:
        return annotation_type_name(args[0])
    if origin in (list, tuple, set, frozenset, Sequence) and args:
        return annotation_type_name(args[0])
    if isinstance(annotation, type):
        return annotation.__name__
    return None
