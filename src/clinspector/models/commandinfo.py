from __future__ import annotations

import dataclasses
import shlex
import subprocess
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

    from clinspector.models import param


@dataclasses.dataclass
class CommandInfo:
    name: str
    """The name of the command."""
    description: str = ""
    """A description for this command."""
    usage: str = ""
    """A formatted string containing a formatted "usage string" (placeholder example)"""
    subcommands: dict[str, CommandInfo] = dataclasses.field(default_factory=dict)
    """A command-name->CommandInfo mapping containing all subcommands."""
    deprecated: bool = False
    """Whether this command is deprecated."""
    epilog: str | None = None
    """Epilog for this command."""
    hidden: bool = False
    """Whether this command is hidden."""
    callback: Callable[..., Any] | None = None
    """A callback for this command."""
    params: list[param.Param] = dataclasses.field(default_factory=list)
    """A list of Params for this command."""
    _parent: CommandInfo | None = dataclasses.field(default=None, repr=False)
    """Reference to parent command (internal use)."""

    def __post_init__(self) -> None:
        """Set parent references for all subcommands."""
        for subcmd in self.subcommands.values():
            subcmd._parent = self

    def __getitem__(self, name: str) -> CommandInfo:
        """Get a subcommand by name."""
        subcmd = self.subcommands[name]
        subcmd._parent = self  # Ensure parent is set
        return subcmd

    @property
    def full_path(self) -> list[str]:
        """Get the full command path as a list of command parts."""
        path: list[str] = []
        current: CommandInfo | None = self

        # Walk up the parent chain
        while current:
            if current.name:
                path.insert(0, current.name)
            current = current._parent

        return path

    @property
    def full_command(self) -> str:
        """Get the full command string including all parents."""
        return " ".join(self.full_path)

    def execute_callback(self, **kwargs: Any) -> Any:
        """Execute this command's callback with the given arguments.

        Args:
            **kwargs: Arguments to pass to the callback

        Returns:
            Result of the callback function

        Raises:
            ValueError: If the command has no callback
        """
        if not self.callback:
            msg = f"Command '{self.full_command}' has no callback"
            raise ValueError(msg)

        return self.callback(**kwargs)

    def build_cli_command(self, args: dict[str, Any] | None = None) -> list[str]:
        """Build the command line parts for execution.

        Args:
            args: Dictionary of parameter name to value mappings

        Returns:
            List of command parts ready for subprocess execution
        """
        args = args or {}
        cmd_parts = self.full_path.copy()
        for p in self.params:
            value = args.get(p.name)
            if value is None:
                continue
            if p.opts:
                if p.is_flag:
                    if value:
                        cmd_parts.append(p.opts[0])
                else:
                    cmd_parts.append(p.opts[0])
                    cmd_parts.append(str(value))
            else:
                cmd_parts.append(str(value))

        return cmd_parts

    def execute_cli(
        self,
        args: dict[str, Any] | None = None,
        capture_output: bool = False,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Execute this command as a CLI process.

        Args:
            args: Dictionary of parameter name to value mappings
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise exception if command fails
            env: Environment variables to set for the process

        Returns:
            Completed process with results

        Raises:
            subprocess.CalledProcessError: If check=True and process returns non-zero
        """
        cmd_parts = self.build_cli_command(args)
        return subprocess.run(
            cmd_parts,
            text=True,
            capture_output=capture_output,
            check=check,
            env=env,
        )

    def execute_shell(
        self,
        args: dict[str, Any] | None = None,
        capture_output: bool = False,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Execute this command via shell (allows pipes, redirects, etc).

        Args:
            args: Dictionary of parameter name to value mappings
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise exception if command fails
            env: Environment variables to set for the process

        Returns:
            Completed process with results

        Raises:
            subprocess.CalledProcessError: If check=True and process returns non-zero
        """
        cmd_parts = self.build_cli_command(args)
        cmd_str = " ".join(shlex.quote(part) for part in cmd_parts)
        return subprocess.run(
            cmd_str,
            text=True,
            capture_output=capture_output,
            check=check,
            env=env,
            shell=True,
        )


if __name__ == "__main__":
    from pprint import pprint

    info = CommandInfo("A", "B")
    pprint(info)
