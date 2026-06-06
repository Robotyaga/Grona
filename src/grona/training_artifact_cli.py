"""CLI demo for training artifact bundle creation and conservative writing."""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence

from .training_artifacts import (
    TrainingArtifactWriteConfig,
    TrainingArtifactWriter,
    build_demo_training_artifact_bundle,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Print or write the deterministic training artifact bundle demo."""
    args = parse_args(argv)
    if args.artifact_write and not args.artifact_output_dir:
        print("Error: --artifact-write requires --artifact-output-dir.")
        return 2
    print(format_training_artifact_demo(argv))
    return 0


def format_training_artifact_demo(argv: Sequence[str] | None = None) -> str:
    """Return deterministic demo output for an in-memory artifact bundle."""
    args = parse_args(argv)
    bundle = build_demo_training_artifact_bundle()
    readme = bundle.get_artifact("README.md")
    config = bundle.get_artifact("config/training_config.json")
    lines = [
        "Training artifact bundle demo",
        "Execution: config only; no model loading, no training, no files, no APIs by default.",
        "",
        bundle.to_text(),
        "",
        "README preview:",
        readme.content if readme else "missing",
        "",
        "Training config preview:",
        config.content if config else "missing",
    ]
    if args.artifact_output_dir:
        report = TrainingArtifactWriter().write(
            bundle,
            args.artifact_output_dir,
            TrainingArtifactWriteConfig(
                dry_run=not args.artifact_write,
                overwrite=args.artifact_overwrite,
                create_parents=args.artifact_write,
                metadata={"cli_demo": True},
            ),
        )
        lines.extend(("", "Writer report:", report.to_text()))
    else:
        lines.extend(("", "Writer report:", "dry-run only; no output directory was requested."))
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None):
    """Parse artifact demo flags while ignoring unrelated top-level flags."""
    parser = ArgumentParser(add_help=False)
    parser.add_argument("--training-artifact-demo", action="store_true")
    parser.add_argument("--artifact-output-dir")
    parser.add_argument("--artifact-write", action="store_true")
    parser.add_argument("--artifact-overwrite", action="store_true")
    parsed, _unknown = parser.parse_known_args(tuple(argv or ()))
    return parsed
