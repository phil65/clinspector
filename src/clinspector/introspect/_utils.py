"""Helpers shared by the framework introspection modules."""

from __future__ import annotations

from collections.abc import Sequence
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
