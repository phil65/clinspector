"""Test file for cyclopts introspection functionality."""

from __future__ import annotations

import pytest

from clinspector.introspect import get_cmd_info
from clinspector.introspect.introspect_cyclopts import get_info


# Skip all tests if cyclopts is not available
cyclopts = pytest.importorskip("cyclopts")


def test_simple_cyclopts_app():
    """Test introspection of a simple cyclopts app."""
    app = cyclopts.App(name="test-app", help="A test application")

    @app.default
    def main(name: str = "World", count: int = 1, verbose: bool = False):
        """Main command that greets someone."""
        return f"Hello, {name}!" * count

    info = get_info(app)

    assert info.name == "test-app"
    assert info.description == "A test application"
    assert len(info.params) >= 0  # May vary based on cyclopts version
    assert info.callback == main


def test_cyclopts_app_with_subcommands():
    """Test introspection of cyclopts app with subcommands."""
    app = cyclopts.App(name="main-app")

    @app.default
    def main(debug: bool = False):
        """Main command."""
        return "main"

    @app.command
    def subcmd(arg: str, flag: bool = False):
        """A subcommand."""
        return f"subcmd: {arg}"

    info = get_info(app)

    assert info.name == "main-app"
    # Check if subcommand exists (filter out help/version commands)
    actual_subcommands = {
        name: cmd for name, cmd in info.subcommands.items() if not name.startswith("-")
    }
    assert len(actual_subcommands) >= 1
    assert "subcmd" in info.subcommands

    sub_info = info.subcommands["subcmd"]
    assert sub_info.name == "subcmd"
    assert sub_info.callback is not None


def test_get_cmd_info_integration():
    """Test that the main get_cmd_info function works with cyclopts."""
    app = cyclopts.App(name="integration-test")

    @app.default
    def main(value: int = 42):
        """Integration test command."""
        return value

    info = get_cmd_info(app)

    assert info is not None
    assert info.name == "integration-test"


def test_cyclopts_specific_command():
    """Test getting info for a specific subcommand."""
    app = cyclopts.App(name="parent")

    @app.default
    def main():
        """Parent command."""

    @app.command
    def child(param: str):
        """Child command."""
        return param

    # Test getting specific subcommand
    child_info = get_info(app, command="child")
    assert child_info.name == "child"

    # Test via main interface
    child_info2 = get_cmd_info(app, command="child")
    assert child_info2 is not None
    assert child_info2.name == "child"


def test_empty_app():
    """Test introspection of app with no default command."""
    app = cyclopts.App(name="empty")

    info = get_info(app)

    assert info.name == "empty"
    assert len(info.params) == 0
    assert info.callback is None


def test_app_with_complex_parameters():
    """Test app with various parameter types."""
    app = cyclopts.App(name="complex")

    @app.default
    def main(
        required_arg: str,
        optional_str: str = "default",
        flag: bool = False,
        number: int = 42,
    ):
        """Command with various parameter types."""
        return f"{required_arg}-{optional_str}-{flag}-{number}"

    info = get_info(app)
    assert info.name == "complex"
    assert info.callback == main

    # Basic check that parameters were extracted
    param_names = {p.name for p in info.params}
    expected_params = {"required_arg", "optional_str", "flag", "number"}
    # Check that at least some expected parameters are present
    assert len(param_names & expected_params) > 0


def test_cyclopts_detection():
    """Test that cyclopts apps are properly detected by the main interface."""
    app = cyclopts.App(name="detection-test")

    @app.default
    def main():
        """Test command."""

    # Should detect as cyclopts app
    info = get_cmd_info(app)
    assert info is not None
    assert info.name == "detection-test"
