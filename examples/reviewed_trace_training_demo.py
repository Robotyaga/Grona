"""Run the deterministic reviewed trace training demo."""

from grona.reviewed_trace_training_cli import format_reviewed_trace_training_demo


def main() -> None:
    """Print reviewed trace training candidate output without writing files."""
    print(format_reviewed_trace_training_demo())


if __name__ == "__main__":
    main()
