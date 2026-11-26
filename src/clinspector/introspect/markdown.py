import importlib.util
from typing import TYPE_CHECKING, Any

from clinspector import get_cmd_info


if TYPE_CHECKING:
    from collections.abc import Iterator

    from minijinja import Environment

    from clinspector.models.commandinfo import CommandInfo


def _get_jinja_env() -> Environment:
    """Get a configured MiniJinja environment."""
    if not importlib.util.find_spec("minijinja"):
        msg = "minijinja is required for markdown generation. Install 'clinspector[markdown]'."
        raise ImportError(msg)

    from minijinja import Environment

    # Output is Markdown, so no HTML escaping.
    env = Environment(
        auto_escape_callback=lambda _name: None,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.add_template("param", _PARAM_TEMPLATE)
    env.add_template("command", _COMMAND_TEMPLATE)
    return env


# Template definitions
_PARAM_TEMPLATE = """
{% if param.param_type_name == "argument" or not param.opts %}
### {{ param.name | upper }}
{% else %}
### {{ param.opt_str }}
{% endif %}

{% if param.required %}
**REQUIRED**
{% endif %}
{% if param.envvar %}
Environment variable: {{ param.envvar }}
{% endif %}
{% if param.multiple %}
**Multiple values allowed.**
{% endif %}
{% if param.default is not none and param.default not in ([], "") %}
**Default:** {{ param.default }}
{% endif %}
{% if param.choices %}
**Choices:** {{ param.choices | join(", ") }}
{% endif %}
{% if param.is_flag %}
**Flag**
{% endif %}
{% if param.help %}
{{ param.help }}
{% endif %}
"""

_COMMAND_TEMPLATE = """
# {{ info.name }}

{{ info.description }}

```
{{ info.usage }}
```

{% for param in params %}
{% include "param" %}
{% endfor %}
"""


def _iter_commands(info: CommandInfo, recursive: bool) -> Iterator[CommandInfo]:
    yield info
    if recursive:
        for sub in info.subcommands.values():
            if not sub.hidden:
                yield from _iter_commands(sub, recursive)


def get_cmd_markdown(
    instance: Any,
    command: str | None = None,
    include_subcommands: bool = False,
) -> str:
    """Generate markdown documentation for a command.

    Hidden parameters and subcommands are left out.

    Args:
        instance: A CLI app instance (Typer, Click, etc.)
        command: Optional specific command to document (supports dot notation)
        include_subcommands: Whether to include documentation for (nested) subcommands

    Returns:
        Formatted markdown string with command documentation
    """
    info = get_cmd_info(instance, command)
    if not info:
        return ""

    env = _get_jinja_env()
    return "\n".join(
        env.render_template(
            "command",
            info=cmd,
            params=[p for p in cmd.params if not p.hidden],
        )
        for cmd in _iter_commands(info, include_subcommands)
    )
