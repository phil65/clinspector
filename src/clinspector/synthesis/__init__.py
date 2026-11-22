"""Generate CLI applications from `CommandInfo` objects."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from clinspector.models.param import Param


_HELP_OPTS = {"-h", "--help"}


def is_help_param(param: Param) -> bool:
    """Whether the param is an (auto-generated) help option.

    Frameworks add their own help option, so these are skipped when synthesizing.
    """
    return param.is_flag and bool(param.opts) and set(param.opts) <= _HELP_OPTS
