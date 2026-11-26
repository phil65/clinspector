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


async def test_man_get_command_help_fetches_page(monkeypatch):
    """The man page is fetched over HTTP and parsed (anyenv 3 response API)."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading

    from clinspector.help_providers.man_pages import ManPageProvider

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = MAN_PAGE.encode()
            self.send_response(200 if self.path == "/1/ls" else 404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, args=(0.05,), daemon=True).start()
    try:
        monkeypatch.setattr(
            ManPageProvider, "BASE_URL", f"http://127.0.0.1:{server.server_address[1]}"
        )
        help_info = await ManPageProvider().get_command_help("ls(1)")
    finally:
        server.shutdown()
        server.server_close()
    assert help_info.name == "ls"
    assert help_info.description.startswith("list directory contents")
