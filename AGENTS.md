# AGENTS.md

## Overview

CLInspector introspects Python CLI applications (Typer, Click, Cleo, Cappa, Cyclopts,
argparse) and turns their command tree into framework-neutral dataclasses
(`CommandInfo` / `Param`). It can also go the other way (synthesize a CLI app from a
`CommandInfo`), render Markdown docs for a command, and fetch help from tldr/man pages.
Its main consumer is mknodes (CLI documentation nodes), so treat the public API
(`get_cmd_info`, `CommandInfo`, `Param` and their fields) as stable.

## Architecture

- `src/clinspector/__init__.py`: public API: `get_cmd_info`, `CommandInfo`, `Param`, `__version__`.
- `src/clinspector/models/`: the core data model.
  - `commandinfo.py`: `CommandInfo` dataclass (name, description, usage, params,
    `subcommands` dict, callback, parent link). `info["sub"]` returns a subcommand;
    `full_path`, `build_cli_command`, `execute_cli`, `execute_shell`.
  - `param.py`: frozen `Param` dataclass (opts, nargs, is_flag, multiple, type, ...).
- `src/clinspector/introspect/`: framework → model.
  - `__init__.py`: `get_cmd_info(instance, command=None)` dispatches on the instance type.
    Each framework is checked with `importlib.util.find_spec` and imported lazily, so
    every framework is optional. Order matters: Typer before Click (Typer wraps Click).
  - `introspect_<framework>.py`: one module per framework, each exposing
    `get_info(instance, command=None)` (cappa: `get_info(cls)`) plus a recursive `parse`.
  - `markdown.py`: `get_cmd_markdown()` renders a command via Jinja2 (`markdown` extra).
  - `cliparser.py`: experimental parser of raw `--help` text into schemez/pydantic models.
    Not imported by the package `__init__`.
- `src/clinspector/synthesis/`: model → framework (`synth_click.create_group`,
  `synth_typer.create_app`, `synth_cleo.create_app`, `synth_argparse.create_parser`,
  `synth_cappa.create_class`). Not exported from the package root. `synth_cappa` is
  rudimentary and does not produce working fields.
- `src/clinspector/help_providers/`: external help sources. `base.py` defines the
  `HelpProvider` protocol and `CommandHelp`/`Example`; `tldr_pages.py` (`tldr` extra)
  and `man_pages.py` (fetches via `anyenv`) implement it. All async.
- `src/clinspector/log.py`: `get_logger` helper.

## Where to look

| Task | File/dir |
|------|----------|
| Support a new CLI framework | new `introspect/introspect_<fw>.py` + dispatch in `introspect/__init__.py` + extra in `pyproject.toml` |
| Fix wrong param data for a framework | `introspect/introspect_<fw>.py` (`_parse_param` / `parse`) |
| Add a field to the model | `models/param.py` or `models/commandinfo.py`, then all introspectors |
| Markdown output | `introspect/markdown.py` |
| Generate a CLI from `CommandInfo` | `synthesis/synth_<fw>.py` |
| tldr / man page help | `help_providers/` |
| Tests | `tests/` (`conftest.py` holds the argparse fixture) |

## Commands

```bash
uv sync --all-extras                 # setup (CI: --no-group docs --no-group lint)
uv run pytest                        # tests (duty: `test`)
uvx ruff check . && uvx ruff format --check .
uv run ty check                      # type check; checks src/ only ([tool.ty.src])
uv run deptry src                    # dependency hygiene
uv run mkdocs-mknodes build          # docs (duty: `build`); serve: uv run mkdocs-mknodes serve
uv build
uvx duty lint                        # ruff fix + format + ty (duties.py; duty is not a dependency)
```

Pre-commit hooks (prek) run ruff, ty, tombi format and pytest on commit.
Releases: `uvx duty version <bump>` bumps, commits and tags; the tag triggers the
PyPI release job in `.github/workflows/build.yml`.

## Conventions

- Python >= 3.13, `from __future__ import annotations` everywhere, Google-style docstrings,
  line length 100, ruff with preview rules.
- Models are plain dataclasses (no pydantic), with attribute docstrings below each field.
- Framework imports are lazy (inside functions or behind `find_spec`) so that importing
  `clinspector` never requires an optional framework. Keep it that way.
- Typer introspection must work across typer versions (see the `type_descriptor`
  fallback in `introspect_typer.py`).
- Tests use pytest 9 (`[tool.pytest]` table); optional frameworks are skipped with
  `pytest.importorskip`. `tests/resources/` and `tests/testresources/` hold sample help
  texts.
- Use targeted `# ty: ignore[rule]` only for real checker limitations.

## Pitfalls

- Copier-managed project (`.copier-answers.yml`, template `copier-phil65`): workflows,
  `duties.py`, `.pre-commit-config.yaml`, `mkdocs.yml` and most of `pyproject.toml`
  come from the template. Update with `copier update` rather than hand-editing;
  add dependencies below the `# Only add below (Copier)` markers.
- Framework support lives in extras (`typer`, `click`, `cleo`, `cappa`, `cyclopts`,
  `markdown`, `tldr`, `man-pages`, `all`). Note `all` does not include `cyclopts`.
- CI tests Python 3.13-3.15 on Linux/macOS/Windows; 3.15 is allowed to fail.
- The docs site is the mkdocs-mknodes default site: README.md is the index page, the
  rest (API, CLI, dev pages) is generated. `docs/` is empty on purpose.
- `help_providers` hit the network (tldr pages, man page sites).
- `uv.lock` is gitignored.
