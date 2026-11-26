"""CLInspector: main package.

Introspect Python CLI apps (Typer, Click, Cleo, Cappa, Cyclopts, argparse) into structured data.
"""

from importlib.metadata import version

__version__ = version("clinspector")
__title__ = "CLInspector"

__author__ = "Philipp Temminghoff"
__author_email__ = "philipptemminghoff@googlemail.com"
__copyright__ = "Copyright (c) 2024 Philipp Temminghoff"
__license__ = "MIT"
__url__ = "https://github.com/phil65/clinspector"


from clinspector.introspect import get_cmd_info
from clinspector.introspect.help_text import parse_help_text
from clinspector.models.commandinfo import CommandInfo
from clinspector.models.param import Param

__all__ = ["CommandInfo", "Param", "__version__", "get_cmd_info", "parse_help_text"]
