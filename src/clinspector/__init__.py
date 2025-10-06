"""CLInspector: A library to parse CLI output into structured data."""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("clinspector")
__title__ = "CLInspector"
__description__ = "A library to parse CLI output into structured data."
__author__ = "Philipp Temminghoff"
__author_email__ = "philipptemminghoff@googlemail.com"
__copyright__ = "Copyright (c) 2024 Philipp Temminghoff"
__license__ = "MIT"
__url__ = "https://github.com/phil65/clinspector"


from clinspector.introspect import get_cmd_info
from clinspector.models.commandinfo import CommandInfo
from clinspector.models.param import Param

__all__ = ["CommandInfo", "Param", "__version__", "get_cmd_info"]
