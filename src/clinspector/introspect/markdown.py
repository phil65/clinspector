from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING, Any

from clinspector import get_cmd_info


if TYPE_CHECKING:
    from collections.abc import Iterator

    from jinja2 import Environment

    from clinspector.models.commandinfo import CommandInfo


def _get_jinja_env() -> Environment:
    """Get a configured Jinja2 environment."""
    if not importlib.util.find_spec("jinja2"):
        msg = "jinja2 is required for markdown generation. Install 'clinspector[markdown]'."
        raise ImportError(msg)

    from jinja2 import Environment

    # Output is Markdown, so no HTML escaping.
    return Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)


# Template definitions
_PARAM_TEMPLATE = """
{% if param.param_type_name == "argument" or not param.opts %}
### {{ param.name.upper() }}
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
{% if param.default is not none and param.default not in ((), [], "") %}
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
{{ param_template.render(param=param) }}
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
    param_template = env.from_string(_PARAM_TEMPLATE)
    command_template = env.from_string(_COMMAND_TEMPLATE)
    return "\n".join(
        command_template.render(
            info=cmd,
            params=[p for p in cmd.params if not p.hidden],
            param_template=param_template,
        )
        for cmd in _iter_commands(info, include_subcommands)
    )
