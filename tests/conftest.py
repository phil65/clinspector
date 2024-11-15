from __future__ import annotations

import argparse
from datetime import datetime

import pytest


DESCRIPTION = "Sample program demonstrating various argument types"
EPILOG = "Example epilog text that appears at the bottom of help"


@pytest.fixture
def example_argparser() -> argparse.ArgumentParser:
    """Create and return a sample argument parser with various argument types."""
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Positional argument
    parser.add_argument(
        "input_file",
        help="Input file to process",
    )

    # Optional arguments with different types
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        default=42,
        help="Sample integer value",
    )

    parser.add_argument(
        "--enable-feature",
        action="store_true",
        help="Enable a specific feature",
    )

    parser.add_argument(
        "-m",
        "--mode",
        choices=["fast", "slow", "auto"],
        default="auto",
        help="Operation mode",
    )

    parser.add_argument(
        "-d",
        "--date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        help="Date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level",
    )

    return parser
