"""tldr-pages provider implementation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from functools import cached_property
import re
from typing import TYPE_CHECKING

from clinspector.help_providers.base import CommandHelp, Example, HelpProvider


if TYPE_CHECKING:
    from types import ModuleType


@dataclass
class TldrExample:
    """Example collected during parsing."""

    description: str
    command: str = ""
    placeholders: dict[str, str] = field(default_factory=dict)

    def to_example(self) -> Example:
        """Convert to CommandInfo Example."""
        return Example(
            description=self.description,
            command=self.command,
            placeholders=self.placeholders,
        )


class TldrProvider(HelpProvider):
    """Provider for tldr-pages help."""

    def __init__(self):
        """Initialize provider."""
        self._cache_initialized = False
        self._init_lock = asyncio.Lock()
        self._loop = asyncio.get_event_loop()

    @cached_property
    def _client(self) -> ModuleType:
        """Lazy load the tldr client module."""
        import tldr

        return tldr

    async def _ensure_cache(self):
        """Initialize cache if needed."""
        if self._cache_initialized:
            return

        async with self._init_lock:
            if not self._cache_initialized:
                await self._loop.run_in_executor(None, self._client.update_cache)
                self._cache_initialized = True

    def _clean_command_name(self, cmd: str) -> str:
        """Remove language suffix from command name."""
        return cmd.split(" (")[0] if " (" in cmd else cmd

    def _parse_page(self, lines: list[bytes], platform: str = "") -> CommandHelp:
        """Parse a tldr page into CommandHelp."""
        examples: list[Example] = []
        name = ""
        description = ""
        current: TldrExample | None = None

        for line_bytes in lines:
            line = line_bytes.decode().strip()

            if line.startswith("# "):
                name = line.removeprefix("# ")
            elif line.startswith("> "):
                description = line.removeprefix("> ")
            elif line.startswith("- "):
                if current:
                    examples.append(current.to_example())
                current = TldrExample(description=line.removeprefix("- "))
            elif line.startswith("`") and current:
                cmd = line.strip("`")
                placeholders: dict[str, str] = {}
                for match in re.finditer(r"\{\{(.+?)\}\}", cmd):
                    placeholders[match.group(1)] = ""
                current.command = cmd
                current.placeholders = placeholders

        if current:
            examples.append(current.to_example())

        return CommandHelp(
            name=name,
            description=description,
            examples=examples,
            platform=platform,
        )

    async def get_command_help(self, command: str) -> CommandHelp:
        """Get help for a command from tldr."""
        await self._ensure_cache()

        for platform_name in ["common", "windows", "linux", "osx"]:
            try:
                result = await self._loop.run_in_executor(
                    None,
                    lambda p=platform_name: self._client.get_page_for_platform(
                        command, p, None, "en"
                    ),
                )
                if result:
                    return self._parse_page(result, platform_name)
            except Exception as exc:  # noqa: BLE001
                print(f"Error fetching {command} for {platform_name}: {exc}")
                continue

        msg = f"No help found for command: {command}"
        raise ValueError(msg)

    async def search_commands(self, query: str) -> list[str]:
        """Search for commands matching query."""
        await self._ensure_cache()

        commands = await self._loop.run_in_executor(None, self._client.get_commands)
        return [
            self._clean_command_name(cmd)
            for cmd in commands
            if query.lower() in self._clean_command_name(cmd).lower()
        ]

    async def list_commands(self) -> list[str]:
        """List all available commands."""
        await self._ensure_cache()
        commands = await self._loop.run_in_executor(None, self._client.get_commands)
        return [self._clean_command_name(cmd) for cmd in commands]


if __name__ == "__main__":

    async def main():
        provider = TldrProvider()
        commands = await provider.list_commands()
        print(commands[:10])  # Print first 10 for testing

        help_info = await provider.get_command_help("git")
        print("\nGit command help:")
        print(f"Name: {help_info.name}")
        print(f"Description: {help_info.description}")
        print("\nExamples:")
        for ex in help_info.examples:
            print(f"\n- {ex.description}")
            print(f"  {ex.command}")
            if ex.placeholders:
                print(f"  Placeholders: {ex.placeholders}")

    asyncio.run(main())
