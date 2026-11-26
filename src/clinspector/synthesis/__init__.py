"""Generate CLI applications from `CommandInfo` objects."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


type Handler = Callable[[CommandInfo, dict[str, Any]], Any]
"""Called with the invoked command and its parsed parameter values."""


_HELP_OPTS = {"-h", "--help"}


def is_help_param(param: Param) -> bool:
    """Whether the param is an (auto-generated) help option.

    Frameworks add their own help option, so these are skipped when synthesizing.
    """
    return param.is_flag and bool(param.opts) and set(param.opts) <= _HELP_OPTS
