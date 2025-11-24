from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from pydantic import Field
from schemez import Schema


class ArgumentType(str, Enum):
    """Supported argument types in CLI commands."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    CHOICE = "choice"
    LIST = "list"


class ArgumentStyle(str, Enum):
    """Different styles of CLI arguments."""

    POSIX_SINGLE = "posix_single"  # -h
    POSIX_LONG = "posix_long"  # --help
    GNU_STYLE = "gnu_style"  # --help=value
    WINDOWS = "windows"  # /help


class CLIOption(Schema):
    """Represents a CLI option/flag."""

    name: str
    short_flag: str | None = None
    """Short form flag (e.g., -h)"""
    long_flag: str | None = None
    """Long form flag (e.g., --help)"""
    description: str = ""
    """Description of the option"""
    required: bool = False
    """Whether the option is required"""
    arg_type: ArgumentType = ArgumentType.STRING
    """Type of the argument"""
    default_value: Any | None = None
    """Default value if any"""
    choices: list[str] | None = None
    """Possible values for choice type"""
    multiple: bool = False
    """Whether multiple values are allowed"""


class CLIPositionalArg(Schema):
    """Represents a positional argument."""

    name: str
    description: str = ""
    """Description of the positional argument"""
    required: bool = True
    """Whether the positional argument is required"""
    arg_type: ArgumentType = ArgumentType.STRING
    """Type of the argument"""
    default_value: Any | None = None
    """Default value if any"""
    choices: list[str] | None = None
    """Possible values for choice type"""


class CLISubcommand(Schema):
    """Represents a subcommand in the CLI."""

    name: str
    description: str = ""
    """Description of the subcommand"""
    options: list[CLIOption] = Field(default_factory=list)
    """List of options for this subcommand"""
    positional_args: list[CLIPositionalArg] = Field(default_factory=list)
    """List of positional arguments for this subcommand"""
    subcommands: dict[str, "CLISubcommand"] = Field(default_factory=dict)
    """Nested subcommands"""


class CLIInterface(Schema):
    """Root model representing the entire CLI interface."""

    program_name: str
    description: str = ""
    """Description of the program"""
    version: str | None = None
    """Version information if available"""
    options: list[CLIOption] = Field(default_factory=list)
    """Global options for the program"""
    positional_args: list[CLIPositionalArg] = Field(default_factory=list)
    """Global positional arguments"""
    subcommands: dict[str, CLISubcommand] = Field(default_factory=dict)
    """Available subcommands"""


@dataclass
class ParserPatterns:
    """Common regex patterns for parsing CLI help text."""

    option_pattern: re.Pattern = re.compile(
        r"(?:(-[a-zA-Z]),\s+)?(--[a-zA-Z-]+)?\s*(?:<([^>]+)>|\[([^\]]+)\])?\s*(.*)",
    )
    positional_pattern: re.Pattern = re.compile(
        r"([A-Z_]+(?:\s+[A-Z_]+)*)\s+(?:\(([^)]+)\))?\s*(.*)",
    )
    subcommand_pattern: re.Pattern = re.compile(
        r"^\s*(\w+)(?:\s+([^:\n]+))(?::\s*(.*))?$",
        re.MULTILINE,
    )


class CLIHelpParser:
    """Parser for CLI help text."""

    def __init__(self) -> None:
        self.patterns = ParserPatterns()

    def parse_help_text(self, help_text: str) -> CLIInterface:
        """Parse CLI help text and return a structured interface description."""
        lines = help_text.split("\n")
        program_name = self._extract_program_name(lines[0])
        desc = self._extract_description(lines)
        cli = CLIInterface(program_name=program_name, description=desc)

        current_section = ""
        for line in lines:
            if not line.strip():
                continue

            if line.strip().lower().startswith("options:"):
                current_section = "options"
                continue
            if line.strip().lower().startswith("commands:"):
                current_section = "commands"
                continue

            if current_section == "options":
                self._parse_option_line(line, cli)
            elif current_section == "commands":
                self._parse_subcommand_line(line, cli)

        return cli

    def _extract_program_name(self, first_line: str) -> str:
        """Extract program name from the first line of help text."""
        return words[0] if (words := first_line.split()) else "unknown"

    def _extract_description(self, lines: list[str]) -> str:
        """Extract program description from help text."""
        description_lines = [
            stripped
            for line in lines[1:]
            if (stripped := line.strip()) and stripped.lower() not in ("options:", "commands:")
        ]
        return " ".join(description_lines)

    def _parse_option_line(self, line: str, cli: CLIInterface) -> None:
        """Parse a line containing option information."""
        match = self.patterns.option_pattern.match(line.strip())
        if not match:
            return

        short_flag, long_flag, arg_name, optional_arg, description = match.groups()

        if not (short_flag or long_flag):
            return

        option = CLIOption(
            name=long_flag.lstrip("-") if long_flag else short_flag.lstrip("-"),
            short_flag=short_flag,
            long_flag=long_flag,
            description=description.strip(),
            required=bool(arg_name and not optional_arg),
            arg_type=self._determine_arg_type(arg_name or optional_arg or ""),
        )

        cli.options.append(option)

    def _parse_subcommand_line(self, line: str, cli: CLIInterface) -> None:
        """Parse a line containing subcommand information."""
        match = self.patterns.subcommand_pattern.match(line.strip())
        if not match:
            return

        name, _args, desc = match.groups()
        cli.subcommands[name] = CLISubcommand(name=name, description=desc or "")

    def _determine_arg_type(self, arg_hint: str) -> ArgumentType:
        """Determine argument type based on hint in help text."""
        hint = arg_hint.lower()
        if any(num_type in hint for num_type in ["number", "count", "int"]):
            return ArgumentType.INTEGER
        if any(file_type in hint for file_type in ["file", "path"]):
            return ArgumentType.FILE_PATH
        if any(bool_type in hint for bool_type in ["bool", "flag"]):
            return ArgumentType.BOOLEAN
        return ArgumentType.STRING


if __name__ == "__main__":
    parser = CLIHelpParser()
    help_text = """
    git - the stupid content tracker

    usage: git [--version] [--help] [-C <path>] [-c <name>=<value>]
               [--exec-path[=<path>]] [--html-path] [--man-path] [--info-path]

    options:
        -v, --verbose         be verbose
        --version            show version information
        --help              show help information
        -C <path>           run as if git was started in <path>

    commands:
        clone       Clone a repository into a new directory
        commit      Record changes to the repository
        push        Update remote refs along with associated objects
    """

    cli_interface = parser.parse_help_text(help_text)
