"""CLI demo for the experimental LoRA backend skeleton."""

from __future__ import annotations

from collections.abc import Sequence

from .experimental_training import (
    ExperimentalLoRABackend,
    LoRATrainingSafetyConfig,
    build_demo_lora_training_inputs,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Print the deterministic experimental LoRA backend skeleton demo."""
    _ = argv
    print(format_experimental_lora_backend_demo())
    return 0


def format_experimental_lora_backend_demo() -> str:
    """Return deterministic demo output for the experimental LoRA backend skeleton."""
    _package, plan, bundle = build_demo_lora_training_inputs()
    backend = ExperimentalLoRABackend()
    safety = LoRATrainingSafetyConfig()
    job, readiness = backend.prepare_training_job(
        plan,
        bundle,
        output_dir="outputs/experimental-lora-demo",
        safety_config=safety,
    )
    refusal_message = refusal_preview(backend, plan, bundle, safety)

    return "\n".join(
        (
            "Experimental LoRA backend skeleton demo",
            "Execution: job preview only; no training, no model loading, no downloads, no subprocesses.",
            "Heavy dependencies are checked with find_spec only and are not imported.",
            "",
            backend.to_text(),
            "",
            "Safety config:",
            safety.to_text(),
            "",
            "Dependency report:",
            backend.check_dependencies().to_text(),
            "",
            "Readiness report:",
            readiness.to_text(),
            "",
            "LoRA training job preview:",
            job.to_text(),
            "",
            "Job JSON preview:",
            job.to_json(),
            "",
            "Run refusal preview:",
            refusal_message,
            "",
            "Real training status:",
            "not implemented, not executed, guarded by default",
        )
    )


def refusal_preview(
    backend: ExperimentalLoRABackend,
    plan,
    bundle,
    safety: LoRATrainingSafetyConfig,
) -> str:
    """Return the expected refusal message from guarded execution."""
    try:
        backend.run_training(plan, bundle, "outputs/experimental-lora-demo", safety)
    except (RuntimeError, NotImplementedError) as exc:
        return str(exc)
    return "unexpected: run_training did not refuse"
