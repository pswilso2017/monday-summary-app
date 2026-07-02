#!/usr/bin/env python3
"""Backward-compatible entry point for the monday summary app CLI."""

from monday_summary_app.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
