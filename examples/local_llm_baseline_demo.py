from grona import LocalLLMBaselineRunner, StaticLocalLLMAdapter


def main() -> None:
    adapter = StaticLocalLLMAdapter(mode="weak_monolith")
    runner = LocalLLMBaselineRunner(adapter)
    result = runner.run("Explain sparse routing for a local-first modular AI prototype.")

    print(result.to_text())
    print("\nStable JSON snapshot:")
    print(result.to_json())
    print("\nLM Studio note:")
    print(
        "LMStudioCompletionAdapter is optional and must be explicitly configured by a user; "
        "this demo never calls it."
    )


if __name__ == "__main__":
    main()
