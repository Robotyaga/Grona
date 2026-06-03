"""Basic sparse routing demo for Grona."""

from grona import Expert, SparseRouter


def make_response(label: str):
    def respond(input_vector):
        return f"{label} expert processed {list(input_vector)}"

    return respond


def main() -> None:
    experts = [
        Expert(
            name="memory",
            profile=(0.9, 0.1, 0.2),
            handler=make_response("Memory"),
            description="Handles recall-heavy inputs.",
        ),
        Expert(
            name="planning",
            profile=(0.2, 0.9, 0.3),
            handler=make_response("Planning"),
            description="Handles sequencing and decomposition.",
        ),
        Expert(
            name="synthesis",
            profile=(0.3, 0.3, 0.9),
            handler=make_response("Synthesis"),
            description="Combines signals into a compact answer.",
        ),
    ]

    router = SparseRouter(experts, top_k=2)
    input_vector = (0.25, 0.8, 0.35)

    for decision, output in router.run(input_vector):
        print(f"Activated {decision.expert.name} with score {decision.score:.3f}")
        print(f"  {output}")


if __name__ == "__main__":
    main()
