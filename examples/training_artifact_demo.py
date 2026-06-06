"""Run the deterministic training artifact bundle demo."""

from grona.training_artifact_cli import format_training_artifact_demo


if __name__ == "__main__":
    print(format_training_artifact_demo(("--training-artifact-demo",)))
