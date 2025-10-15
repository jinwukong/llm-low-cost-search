#!/usr/bin/env python3
"""Convenience runner to execute the demo from the repo root.

Usage:
    python run_demo.py "keyword"

This wrapper ensures the repository's parent directory is on sys.path so that
the package `search` can be resolved as `search.demo` when run as a module.
"""

from pathlib import Path
import runpy
import sys


def main() -> None:
    repo_dir = Path(__file__).resolve().parent
    parent = repo_dir.parent

    # Ensure the parent of the repo root is importable as the package root
    # so that `search.demo` can be executed as a module.
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))

    # Forward CLI args to the demo module
    sys.argv = ["search.demo"] + sys.argv[1:]
    runpy.run_module("search.demo", run_name="__main__")


if __name__ == "__main__":
    main()

