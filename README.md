# CLInspector

[![PyPI License](https://img.shields.io/pypi/l/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Package status](https://img.shields.io/pypi/status/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Monthly downloads](https://img.shields.io/pypi/dm/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Distribution format](https://img.shields.io/pypi/format/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Wheel availability](https://img.shields.io/pypi/wheel/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Python version](https://img.shields.io/pypi/pyversions/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Implementation](https://img.shields.io/pypi/implementation/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Releases](https://img.shields.io/github/downloads/phil65/clinspector/total.svg)](https://github.com/phil65/clinspector/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/clinspector)](https://github.com/phil65/clinspector/graphs/contributors)
[![Github Forks](https://img.shields.io/github/forks/phil65/clinspector)](https://github.com/phil65/clinspector/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/clinspector)](https://github.com/phil65/clinspector/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/clinspector)](https://github.com/phil65/clinspector/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/clinspector)](https://github.com/phil65/clinspector/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/clinspector)](https://github.com/phil65/clinspector/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/clinspector)](https://github.com/phil65/clinspector)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/clinspector)](https://github.com/phil65/clinspector/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/clinspector)](https://github.com/phil65/clinspector/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/clinspector)](https://github.com/phil65/clinspector)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/clinspector)](https://github.com/phil65/clinspector)
[![Package status](https://codecov.io/gh/phil65/clinspector/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/clinspector/)
[![PyUp](https://pyup.io/repos/github/phil65/clinspector/shield.svg)](https://pyup.io/repos/github/phil65/clinspector/)

[Read the documentation!](https://phil65.github.io/clinspector/)

CLInspector introspects Python CLI applications and returns their command tree
(commands, subcommands, options and arguments) as plain, framework-independent
dataclasses. Use it to generate CLI documentation, build completions or wrappers,
or analyze CLI interfaces without parsing `--help` output.

## Installation

```bash
pip install clinspector
```

Framework support is optional; install the extras for the frameworks you use:

```bash
pip install "clinspector[click]"      # or: typer, cleo, cappa, cyclopts
pip install "clinspector[all]"        # all frameworks and optional features
pip install "clinspector[markdown]"   # Markdown rendering (jinja2)
pip install "clinspector[tldr]"       # tldr page help provider (also: man-pages)
```

## Quickstart

```python
import click

from clinspector import get_cmd_info


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose: bool) -> None:
    """Example CLI tool."""


@cli.command()
@click.argument("target")
@click.option("--release", is_flag=True, help="Build in release mode")
def build(target: str, release: bool) -> None:
    """Build the project."""


info = get_cmd_info(cli)
print(info.name, "-", info.description)  # cli - Example CLI tool.
for param in info.params:
    print(param.opts, param.help)  # ['-v', '--verbose'] Enable verbose output, ...

build_info = info["build"]  # subcommands via item access
print(build_info.full_command)  # cli build
print([p.name for p in build_info.params])  # ['target', 'release', ...]
```

## Supported frameworks

`get_cmd_info(instance, command=None)` accepts:

- [Typer](https://typer.tiangolo.com/): `typer.Typer` instances
- [Click](https://click.palletsprojects.com/): `click.Command` / `click.Group` instances
- [Cleo](https://cleo.readthedocs.io/): `cleo.application.Application` instances
- [Cappa](https://github.com/DanCardin/cappa): classes decorated with `@cappa.command`
- [Cyclopts](https://github.com/BrianPugh/cyclopts): `cyclopts.App` instances
- [argparse](https://docs.python.org/3/library/argparse.html): `ArgumentParser` instances

Pass `command` to get a specific subcommand directly. Nested subcommands use dot
notation (`"group.sub"`); a leading root command name is ignored (`"cli.group.sub"`).
If no such subcommand exists, the root command is returned. `get_cmd_info` returns
`None` for unsupported objects.

## Data model

`CommandInfo` (`clinspector.CommandInfo`):

- `name`, `description`, `usage`, `epilog`
- `params: list[Param]`
- `subcommands: dict[str, CommandInfo]` (also reachable via `info["name"]`)
- `deprecated`, `hidden`, `callback` (the framework callback, not serialized or compared)
- `full_path` / `full_command`: the command path including parents
- `walk()`: iterate over the command and all nested subcommands
- `to_dict()` / `CommandInfo.from_dict()`: plain-dict (JSON) round trip
- `build_cli_command()`, `execute_cli()`: run the command as a subprocess

`Param` (`clinspector.Param`), among others:

- `name`, `help`, `default`, `opts` (e.g. `["-f", "--flag"]`), `secondary_opts`
- `required`, `is_flag`, `multiple`, `nargs`, `choices`, `metavar`
- `envvar`, `hidden`, `param_type_name` (`"option"` or `"argument"`)
- `type`: normalized type name (`"str"`, `"int"`, `"bool"`, `"path"`, `"choice"`, ...)

## More features

- **Markdown docs**: `clinspector.introspect.markdown.get_cmd_markdown(instance, command=None, include_subcommands=False)`
  renders a command as Markdown (`markdown` extra).
- **Synthesis**: create a CLI from a `CommandInfo`, e.g.
  `clinspector.synthesis.synth_click.create_group`, `synth_typer.create_app`,
  `synth_cleo.create_app`, `synth_argparse.create_parser`, `synth_cappa.create_class`.
  Pass `handler=` (`handler(command_info, values)`) to run code when a command is invoked
  (all except argparse, which only parses).
- **Help providers**: async lookups of command examples from tldr pages
  (`clinspector.help_providers.tldr_pages.TldrProvider`, `tldr` extra) and man pages
  (`clinspector.help_providers.man_pages.ManPageProvider`, `man-pages` extra).
- **Help text parser**: `clinspector.parse_help_text(text)` turns raw `--help` output
  (argparse, click/typer, rich-click, docopt, cement, cliff, plac, fire layouts) into a
  `CommandInfo`. Heuristic: prefer `get_cmd_info` when you have the CLI object.
