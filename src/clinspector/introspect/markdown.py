from __future__ import annotations

import importlib.util
from typing import Any

from clinspector import get_cmd_info


def _get_jinja_env():
    """Get a configured Jinja2 environment."""
    if not importlib.util.find_spec("jinja2"):
        msg = (
            "jinja2 is required for markdown generation. "
            "Install with 'pip install jinja2'"
        )
        raise ImportError(msg)

    from jinja2 import Environment, select_autoescape

    escape = select_autoescape(["html", "xml"])
    env = Environment(autoescape=escape, trim_blocks=True, lstrip_blocks=True)

    # Add custom filters
    env.filters["md_style"] = lambda text, bold=False, italic=False: (
        f"**{text}**" if bold else (f"*{text}*" if italic else text)
    )

    return env


# Template definitions
_PARAM_TEMPLATE = """
### {{ param.opt_str }}

{% if param.required %}
**REQUIRED**
{% endif %}
{% if param.envvar %}
Environment variable: {{ param.envvar }}
{% endif %}
{% if param.multiple %}
**Multiple values allowed.**
{% endif %}
{% if param.default %}
**Default:** {{ param.default }}
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

{% for param in info.params %}
{{ param_template | render(param=param) }}
{% endfor %}
"""

_OUTPUT_TEMPLATE = """
{% if info %}
{{ command_template | render(info=info) }}
{% if include_subcommands %}
{% for sub_name, sub_info in info.subcommands.items() %}
{{ command_template | render(info=sub_info) }}
{% endfor %}
{% endif %}
{% endif %}
"""


def get_cmd_markdown(
    instance: Any,
    command: str | None = None,
    include_subcommands: bool = False,
) -> str:
    """Generate markdown documentation for a command.

    Args:
        instance: A CLI app instance (Typer, Click, etc.)
        command: Optional specific command to document
        include_subcommands: Whether to include documentation for subcommands

    Returns:
        Formatted markdown string with command documentation
    """
    info = get_cmd_info(instance, command)
    if not info:
        return ""

    env = _get_jinja_env()

    # Define render function for templates to use
    def render_template(template_str, **kwargs):
        template = env.from_string(template_str)
        return template.render(**kwargs)

    env.filters["render"] = render_template
    template = env.from_string(_OUTPUT_TEMPLATE)  # Prepare the main template
    return template.render(
        info=info,
        include_subcommands=include_subcommands,
        command_template=_COMMAND_TEMPLATE,
        param_template=_PARAM_TEMPLATE,
    )
