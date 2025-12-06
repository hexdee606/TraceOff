"""
Module entry point for `python -m traceoff`.

This simply delegates execution to the CLI application.
"""

from .cli import app


def main() -> None:
    """
    Run the TraceOff CLI application.
    """
    app()


if __name__ == "__main__":
    main()
