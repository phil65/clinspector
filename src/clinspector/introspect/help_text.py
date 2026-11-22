"""Parse raw `--help` output into a `CommandInfo`.

This is a best-effort, heuristic parser for the common help layouts of argparse, click,
typer, rich-click, docopt, cement, cliff, plac and fire. Use the framework introspection
(`get_cmd_info`) instead whenever the CLI object itself is available.
"""

from __future__ import annotations

import dataclasses
import re

from clinspector.models.commandinfo import CommandInfo
from clinspector.models.param import Param


_USAGE_RE = re.compile(r"^\s*usage:\s*(.*)$", re.IGNORECASE)
_SECTION_RE = re.compile(r"^(?P<title>[A-Za-z][\w ()/-]*):\s*$")
# term and help are separated by at least two spaces (or the term is alone on its line)
_ENTRY_RE = re.compile(r"^(?P<indent>\s+)(?P<term>\S(?:.*?\S)?)(?:\s{2,}(?P<help>\S.*))?$")
_CHOICES_RE = re.compile(r"^[\[{](?P<choices>[^\]}]+[|,][^\]}]+)[\]}]$")
_TOKEN_RE = re.compile(r"\{[^}]*\}|\[[^\]]*\]|<[^>]*>|[^\s,]+")
_DEFAULT_RE = re.compile(r"\[default:\s*(?P<default>[^\]]*)\]", re.IGNORECASE)
_TYPE_HINTS = {
    "int": ("int", "number", "count", "num"),
    "float": ("float",),
    "path": ("file", "path", "dir"),
}


@dataclasses.dataclass
class _Entry:
    term: str
    help: str
    indent: int
    children: list[_Entry] = dataclasses.field(default_factory=list)


def _section_kind(title: str) -> str | None:
    title = title.lower()
    if "example" in title:
        return None
    if "command" in title:
        return "commands"
    if "positional" in title:
        return "positional"
    if "option" in title or "argument" in title or "flag" in title:
        return "options"
    return None


def _parse_entries(lines: list[str]) -> list[_Entry]:
    """Group indented lines into term/help entries (with nested entries for argparse)."""
    entries: list[_Entry] = []
    for line in lines:
        if not (match := _ENTRY_RE.match(line)):
            continue
        indent = len(match["indent"])
        term, help_text = match["term"], match["help"] or ""
        if entries:
            last = entries[-1].children[-1] if entries[-1].children else entries[-1]
            # deeply indented line without own term column: continuation of the help text
            if indent > entries[-1].indent + 4 and not help_text and not term.startswith("-"):
                last.help = f"{last.help} {term}".strip()
                continue
            if indent > entries[-1].indent:
                entries[-1].children.append(_Entry(term, help_text, indent))
                continue
        entries.append(_Entry(term, help_text, indent))
    return entries


def _guess_type(metavar: str) -> str:
    hint = metavar.lower()
    for type_name, words in _TYPE_HINTS.items():
        if any(w in hint for w in words):
            return type_name
    return "str"


def _is_metavar(token: str) -> bool:
    return token.startswith(("<", "[", "{")) or (token.isupper() and token[:1].isalpha())


def _parse_option(entry: _Entry) -> Param | None:
    opts: list[str] = []
    metavar = None
    choices = None
    tokens = _TOKEN_RE.findall(entry.term)
    rest: list[str] = []
    for index, token in enumerate(tokens):
        if token.startswith("-"):
            opt, _, value = token.partition("=")
            if opt not in opts:
                opts.append(opt)
            if value:
                metavar = value.strip("<>")
        elif match := _CHOICES_RE.match(token):
            choices = re.split(r"[|,]", match["choices"])
        elif _is_metavar(token):
            metavar = token.strip("<>[]")
        elif token not in ("|", "/"):
            rest = tokens[index:]  # help text separated by a single space only
            break
    if not opts:
        return None
    long_opts = [o for o in opts if o.startswith("--")]
    name = (long_opts or opts)[0].lstrip("-").replace("-", "_")
    help_text = " ".join([*rest, entry.help]).strip() or None
    default = match["default"] if help_text and (match := _DEFAULT_RE.search(help_text)) else None
    takes_value = bool(metavar or choices)
    return Param(
        name=name,
        opts=opts,
        help=help_text,
        default=default,
        metavar=metavar,
        choices=choices,
        is_flag=not takes_value,
        type=("choice" if choices else _guess_type(metavar or "")) if takes_value else "bool",
    )


def _command_name(term: str, prog: str) -> str | None:
    words = term.split()
    if len(words) > 1 and words[0] in (prog, prog.removesuffix(".py"), "python"):
        words = words[1:]
    name = words[0] if words else ""
    if not name or name.startswith(("-", "<", "[")):
        return None
    return name


def _usage_block(lines: list[str]) -> tuple[str, int, int]:
    """Return the usage text and the line range it occupies (or `("", -1, -1)`)."""
    for i, line in enumerate(lines):
        if not (match := _USAGE_RE.match(line)):
            continue
        parts = [match[1].strip()] if match[1].strip() else []
        end = i + 1
        while end < len(lines) and lines[end].strip() and lines[end][:1].isspace():
            parts.append(lines[end].strip())
            end += 1
        joiner = " " if match[1].strip() else "\n"  # docopt: one usage pattern per line
        return joiner.join(parts), i, end
    return "", -1, -1


def _prog_name(usage: str, lines: list[str]) -> str:
    words = usage.split()
    if words and words[0] == "python" and len(words) > 1:
        return words[1]
    if words:
        return words[0]
    first = next((line.split()[0] for line in lines if line.strip()), "")
    return first.rstrip(".:")


def parse_help_text(text: str) -> CommandInfo:
    """Parse the `--help` output of a CLI program into a `CommandInfo`.

    Recognized sections are options (`Options:`, `optional arguments:`, ...),
    positional arguments (argparse subcommand lists included) and commands.
    Subcommands are returned without params (their help pages are separate).

    Args:
        text: The help text.
    """
    lines = text.expandtabs().splitlines()
    usage, usage_start, usage_end = _usage_block(lines)
    prog = _prog_name(usage, lines)

    sections: list[tuple[str | None, list[str]]] = []
    free_lines: list[tuple[int, str]] = []
    first_section = len(lines)
    current: list[str] | None = None
    for i, line in enumerate(lines):
        if usage_start <= i < usage_end:
            current = None
            continue
        if (match := _SECTION_RE.match(line)) and not line[:1].isspace():
            current = []
            sections.append((_section_kind(match["title"]), current))
            first_section = min(first_section, i)
        elif current is not None and (line[:1].isspace() or not line.strip()):
            current.append(line)
        else:
            current = None
            if line.strip():
                free_lines.append((i, line.strip()))

    # description: text between usage and the first section, else text before the usage
    # (docopt / cement put a title line first). Text after the sections is the epilog.
    after_usage = [t for i, t in free_lines if usage_end <= i < first_section]
    before_usage = [t for i, t in free_lines if i < min(usage_start % len(lines), first_section)]
    description = " ".join(after_usage or before_usage)
    epilog = " ".join(t for i, t in free_lines if i > first_section) or None
    params: list[Param] = []
    subcommands: dict[str, CommandInfo] = {}

    def add_command(name: str | None, help_text: str) -> None:
        if name and name not in subcommands:
            subcommands[name] = CommandInfo(name=name, description=help_text)

    for kind, section_lines in sections:
        entries = _parse_entries(section_lines)
        for entry in entries:
            if kind == "options":
                if param := _parse_option(entry):
                    params.append(param)
            elif kind == "commands":
                add_command(_command_name(entry.term, prog), entry.help)
            elif kind == "positional":
                if match := _CHOICES_RE.match(entry.term):  # argparse subparsers
                    for child in entry.children:
                        add_command(_command_name(child.term, prog), child.help)
                    for name in re.split(r"[|,]", match["choices"]):
                        add_command(name.strip(), "")
                else:
                    name = entry.term.strip("<>[]").lower()
                    params.append(
                        Param(
                            name=name,
                            help=entry.help or None,
                            required=True,
                            param_type_name="argument",
                            metavar=entry.term,
                        )
                    )

    return CommandInfo(
        name=prog,
        description=description,
        usage=usage,
        params=params,
        subcommands=subcommands,
        epilog=epilog,
    )
