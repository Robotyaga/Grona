"""Shared console entrypoint for Grona demos."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from .benchmark_cli import main as benchmark_main
from .benchmark_regression_cli import main as benchmark_regression_main
from .cli import main as cli_main
from .dataset_review_cli import main as dataset_review_main
from .donor_cli import main as donor_main
from .experiment_cli import main as experiment_main
from .experiment_gate_cli import main as experiment_gate_main
from .inference_review_cli import main as inference_review_main
from .jsonl_dataset_cli import main as jsonl_dataset_main
from .local_llm_cli import main as local_llm_main
from .prompt_trace_cli import main as prompt_trace_main
from .reviewed_trace_training_cli import main as reviewed_trace_training_main
from .training_cli import main as training_main
from .training_package_cli import main as training_package_main


def main(argv: Sequence[str] | None = None) -> int:
    """Route top-level demo flags before delegating to the main CLI."""
    args = tuple(sys.argv[1:] if argv is None else argv)
    if "--benchmark-demo" in args:
        return benchmark_main(args)
    if "--benchmark-regression-demo" in args:
        return benchmark_regression_main(args)
    if "--experiment-demo" in args:
        return experiment_main(args)
    if "--experiment-gate-demo" in args or "--experiment-gate-strict-demo" in args:
        return experiment_gate_main(args)
    if "--local-llm-static-demo" in args:
        return local_llm_main(args)
    if "--prompt-trace-demo" in args:
        return prompt_trace_main(args)
    if "--inference-review-demo" in args:
        return inference_review_main(args)
    if "--reviewed-trace-training-demo" in args:
        return reviewed_trace_training_main(args)
    if "--donor-demo" in args:
        return donor_main(args)
    if "--training-export-demo" in args:
        return training_main(args)
    if "--training-package-demo" in args:
        return training_package_main(args)
    if "--jsonl-dataset-demo" in args:
        return jsonl_dataset_main(args)
    if "--dataset-review-demo" in args:
        return dataset_review_main(args)
    return cli_main(args)
