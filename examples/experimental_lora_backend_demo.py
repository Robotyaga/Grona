"""Deterministic example for the experimental LoRA backend skeleton.

This example does not train a model, load a model, import heavy ML libraries,
write files, call external APIs, or execute subprocesses.
"""

from grona import ExperimentalLoRABackend, LoRATrainingSafetyConfig, build_demo_lora_training_inputs


def main() -> None:
    """Print dependency, readiness, job preview, and guarded refusal details."""
    _package, plan, bundle = build_demo_lora_training_inputs()
    backend = ExperimentalLoRABackend()
    safety = LoRATrainingSafetyConfig()
    job, readiness = backend.prepare_training_job(
        plan,
        bundle,
        output_dir="outputs/experimental-lora-demo",
        safety_config=safety,
    )

    print("Experimental LoRA backend example")
    print("Execution: preview only; no real training is performed.")
    print()
    print(backend.check_dependencies().to_text())
    print()
    print(readiness.to_text())
    print()
    print(job.to_text())
    print()
    try:
        backend.run_training(plan, bundle, "outputs/experimental-lora-demo", safety)
    except (RuntimeError, NotImplementedError) as exc:
        print("Guarded run refused as expected:")
        print(exc)


if __name__ == "__main__":
    main()
