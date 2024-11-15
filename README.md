# CLInspector

[![PyPI License](https://img.shields.io/pypi/l/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Package status](https://img.shields.io/pypi/status/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Daily downloads](https://img.shields.io/pypi/dd/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Weekly downloads](https://img.shields.io/pypi/dw/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Monthly downloads](https://img.shields.io/pypi/dm/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Distribution format](https://img.shields.io/pypi/format/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Wheel availability](https://img.shields.io/pypi/wheel/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Python version](https://img.shields.io/pypi/pyversions/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Implementation](https://img.shields.io/pypi/implementation/clinspector.svg)](https://pypi.org/project/clinspector/)
[![Releases](https://img.shields.io/github/downloads/phil65/clinspector/total.svg)](https://github.com/phil65/clinspector/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/clinspector)](https://github.com/phil65/clinspector/graphs/contributors)
[![Github Discussions](https://img.shields.io/github/discussions/phil65/clinspector)](https://github.com/phil65/clinspector/discussions)
[![Github Forks](https://img.shields.io/github/forks/phil65/clinspector)](https://github.com/phil65/clinspector/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/clinspector)](https://github.com/phil65/clinspector/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/clinspector)](https://github.com/phil65/clinspector/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/clinspector)](https://github.com/phil65/clinspector/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/clinspector)](https://github.com/phil65/clinspector/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/clinspector)](https://github.com/phil65/clinspector)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/clinspector)](https://github.com/phil65/clinspector/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/clinspector)](https://github.com/phil65/clinspector/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/clinspector)](https://github.com/phil65/clinspector)
[![Github commits this week](https://img.shields.io/github/commit-activity/w/phil65/clinspector)](https://github.com/phil65/clinspector)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/clinspector)](https://github.com/phil65/clinspector)
[![Github commits this year](https://img.shields.io/github/commit-activity/y/phil65/clinspector)](https://github.com/phil65/clinspector)
[![Package status](https://codecov.io/gh/phil65/clinspector/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/clinspector/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyUp](https://pyup.io/repos/github/phil65/clinspector/shield.svg)](https://pyup.io/repos/github/phil65/clinspector/)

[Read the documentation!](https://phil65.github.io/clinspector/)

# CLInspector Documentation

CLInspector is a library to introspect Python CLI applications and extract their command structure and parameters programmatically.

## Usage

The main entry point is the `get_cmd_info()` function which analyzes a CLI application instance and returns a structured `CommandInfo` object:

```python
from clinspector import get_cmd_info

command_info = get_cmd_info(cli_instance)
```

The function accepts CLI application instances from the following frameworks:

- [Typer](https://typer.tiangolo.com/) - `typer.Typer` instances
- [Click](https://click.palletsprojects.com/) - `click.Group` instances
- [Cleo](https://cleo.readthedocs.io/) - `cleo.Application` instances
- [Cappa](https://github.com/DynamicArray/Cappa) - Classes decorated with `@cappa.command`
- [argparse](https://docs.python.org/3/library/argparse.html) - `ArgumentParser` instances

The extracted information is returned as a `CommandInfo` object containing:

### CommandInfo Fields

- `name: str` - Name of the command
- `description: str` - Description/help text
- `usage: str` - Formatted usage string
- `subcommands: dict[str, CommandInfo]` - Nested subcommands
- `deprecated: bool` - Whether command is marked as deprecated
- `epilog: str | None` - Optional epilog text
- `hidden: bool` - Whether command is hidden
- `params: list[Param]` - List of command parameters

### Param Fields

- `name: str` - Parameter name
- `help: str | None` - Help text
- `default: Any` - Default value
- `opts: list[str]` - Parameter options (e.g. `["-f", "--flag"]`)
- `required: bool` - Whether parameter is required
- `is_flag: bool` - Whether parameter is a flag
- `multiple: bool` - Whether parameter accepts multiple values
- `nargs: int | str | None` - Number of arguments accepted
- `envvar: str | None` - Environment variable name
- `hidden: bool` - Whether parameter is hidden
- `param_type_name: Literal["option", "parameter", "argument"]` - Parameter type
- `type: dict[str, str] | None` - Parameter type information
- `metavar: str | None` - Display name in help text

You can access subcommands using dictionary syntax:

```python
# Get info for "build" subcommand
build_info = command_info["build"]

# Access nested subcommand
nested_info = command_info["group"]["subcommand"]
```
```

The extracted information allows you to:

- Generate documentation automatically
- Build command completion
- Create wrappers and adapters
- Perform static analysis of CLI interfaces
- And more!

Example output for a click command:

```python
CommandInfo(
    name="cli",
    description="Example CLI tool",
    usage="cli [OPTIONS] COMMAND [ARGS]...",
    params=[
        Param(name="verbose", help="Enable verbose output", opts=["-v", "--verbose"])
    ],
    subcommands={
        "build": CommandInfo(
            name="build",
            description="Build the project",
            params=[...]
        )
    }
)
```
