from __future__ import annotations

from importlib.metadata import version

__version__ = version("clinspector")

from clinspector.introspect import get_cmd_info
from clinspector.models.commandinfo import CommandInfo
from clinspector.models.param import Param

__all__ = ["CommandInfo", "Param", "__version__", "get_cmd_info"]
