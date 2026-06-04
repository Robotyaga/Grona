"""Shared console entrypoint for Grona demos."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from .benchmark_cli import main as benchmark_main
from .cli import main as cli_main


def main(argv: Sequence[str] | None = None) -> int:
    """Route top-level demo flags before delegating to the main CLI."""
    args = tuple(sys.argv[1:] if argv is None else argv)
    if "--benchmark-demo" in args:
        return benchmark_main(args)
    return cli_main(args)
