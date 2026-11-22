"""Offline tests for the help provider page parsers."""

from __future__ import annotations

from clinspector.help_providers.tldr_pages import TldrProvider


TLDR_PAGE = b"""# tar

> Archiving utility.
> Often combined with a compression method.
> More information: <https://www.gnu.org/software/tar>.

- [c]reate an archive and write it to a [f]ile:

`tar cf {{path/to/target.tar}} {{path/to/file1 path/to/file2 ...}}`

- E[x]tract a (compressed) archive [f]ile into the current directory:

`tar xf {{path/to/source.tar[.gz|.bz2|.xz]}}`
"""

MAN_PAGE = """NAME
       ls - list directory contents

SYNOPSIS
       ls [OPTION]... [FILE]...

DESCRIPTION
       List  information  about  the FILEs (the current directory by default).  Sort en-
       tries alphabetically if none of -cftuvSUX nor --sort is specified.

       Mandatory arguments to long options are mandatory for short options too.
"""


def test_tldr_parse_page():
    help_info = TldrProvider()._parse_page(TLDR_PAGE.splitlines(), platform="common")
    assert help_info.name == "tar"
    assert help_info.description == "Archiving utility. Often combined with a compression method."
    assert len(help_info.examples) == 2  # noqa: PLR2004
    example = help_info.examples[0]
    assert example.command.startswith("tar cf")
    assert set(example.placeholders) == {"path/to/target.tar", "path/to/file1 path/to/file2 ..."}
    assert help_info.platform == "common"


def test_man_parse_page():
    from clinspector.help_providers.man_pages import ManPageProvider

    provider = ManPageProvider()
    assert provider._parse_man_ref("git(1)").name == "git"
    assert provider._parse_man_ref("printf(3)").number == "3"
    help_info = provider._parse_page(MAN_PAGE)
    assert help_info.name == "ls"
    paragraphs = help_info.description.split("\n\n")
    assert paragraphs[0] == "list directory contents"
    assert "Sort entries alphabetically if none of -cftuvSUX" in paragraphs[1]
    assert paragraphs[2].startswith("Mandatory arguments")
