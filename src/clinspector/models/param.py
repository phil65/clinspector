from __future__ import annotations

import dataclasses
from typing import Any, Literal


ParamTypeName = Literal["option", "argument"]


@dataclasses.dataclass
class Param:
    """Framework-independent description of a CLI parameter (option or argument)."""

    count: bool = False
    """Whether the parameter increments an integer."""
    default: Any = None
    """The default value of the parameter."""
    envvar: str | None = None
    """The environment variable name for this parameter."""
    flag_value: bool = False
    """Value used for this flag if enabled."""
    help: str | None = None
    """A formatted help text for this parameter."""
    hidden: bool = False
    """Whether this parameter is hidden."""
    is_flag: bool = False
    """Whether the parameter is a flag."""
    multiple: bool = False
    """Whether the parameter is accepted multiple times and recorded."""
    name: str = ""
    """The name of this parameter."""
    nargs: int | str | None = 1
    """The number of arguments this parameter matches. (Argparse may return * / ?)"""
    opts: list[str] = dataclasses.field(default_factory=list)
    """Options for this parameter."""
    param_type_name: ParamTypeName = "option"
    """Whether this parameter is an option or a positional argument."""
    prompt: Any = None
    """Whether user is prompted for this parameter."""
    required: bool = False
    """Whether the parameter is required."""
    secondary_opts: list[str] = dataclasses.field(default_factory=list)
    """Secondary options for this parameter (e.g. `--no-flag`)."""
    type: str | None = None
    """Name of the value type (`"str"`, `"int"`, `"float"`, `"bool"`, `"path"`, ...)."""
    expose_value: bool = True
    """Whether value is passed onwards to the command callback and stored in context."""
    is_eager: bool = False
    """Whether the param is eager."""
    metavar: str | None = None
    """How value is represented in the help page."""
    choices: list[str] | None = None
    """List of valid choices for this parameter."""

    @property
    def opt_str(self) -> str:
        """A formatted and sorted string containing the the options."""
        return ", ".join(f"`{i}`" for i in reversed(self.opts))

    @property
    def is_option(self) -> bool:
        """Whether this parameter is an option (as opposed to a positional argument)."""
        return self.param_type_name == "option"

    def to_dict(self) -> dict[str, Any]:
        """Return a dict representation of this param."""
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Param:
        """Create a Param from a dict (as returned by `to_dict`). Unknown keys are ignored."""
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in fields})
