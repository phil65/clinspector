"""Module for different CLI help providers."""

from __future__ import annotations

import dataclasses
from typing import Protocol


@dataclasses.dataclass
class Example:
    """An example command usage with description."""

    description: str
    """Description of what the example does."""
    command: str
    """The actual command with placeholders."""
    placeholders: dict[str, str]
    """Mapping of placeholder names to descriptions."""


class HelpProvider(Protocol):
    """Protocol for CLI help providers."""

    async def get_command_help(self, command: str) -> CommandHelp:
        """Get help information for a command."""
        ...

    async def search_commands(self, query: str) -> list[str]:
        """Search for commands matching query."""
        ...

    async def list_commands(self) -> list[str]:
        """List all available commands."""
        ...


@dataclasses.dataclass
class CommandHelp:
    """Help information for a command."""

    name: str
    """The command name."""
    description: str
    """A description of what the command does."""
    examples: list[Example]
    """Usage examples."""
    platform: str = ""
    """Platform this help is for (linux, osx etc)."""
    language: str = "en"
    """Language of the help text."""
