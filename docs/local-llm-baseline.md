# Local LLM Baseline

The local LLM baseline layer prepares an explicit comparison target for future experiments. It is separate from donor proposals and from Grona routing.

This foundation is intentionally small and honest:

- the default demo uses a deterministic static adapter only
- tests and CI do not call LM Studio, external APIs, downloads, training, or heavy dependencies
- the optional LM Studio-compatible adapter uses the Python standard library
- real model calls only happen when a caller explicitly constructs and runs that adapter
- baseline output is comparison material, not trusted knowledge
- this layer does not prove that Grona is better or worse than a local model

## How It Differs From Donor Proposals

`DonorModelAdapter` is a proposal source. It can suggest summaries, hints, or raw untrusted `knowledge_seed` candidates that must still pass validation, review, benchmarks, and human judgment.

`LocalLLMAdapter` is a baseline answer source. It receives the whole task directly and produces a direct answer-like response for experiment comparison. It does not expose Grona's sparse route, selected modules, context construction trace, or GrowthEngine signals.

This distinction matters:

- donor output may become candidate material after review
- local LLM baseline output is used to compare experiment traces
- neither path is trusted by default

## Main Types

- `LocalLLMRequest`: prompt, model label, temperature, max tokens, and metadata.
- `LocalLLMResponse`: response text, model label, timing, token metadata, and error state.
- `LocalLLMAdapter`: provider protocol for future static, local, or API-compatible adapters.
- `StaticLocalLLMAdapter`: deterministic offline adapter for tests and demos.
- `LMStudioCompletionAdapter`: optional OpenAI-compatible local completion adapter for explicit LM Studio-style experiments.
- `LocalLLMBaselineRunner`: runs a baseline request and returns a structured result.

## Prompt Trace Layer

`PromptTemplate`, `PromptBuilder`, and `InferenceTrace` sit before and after adapter calls. They make prompt construction and response provenance explicit:

```text
RoutingDecision + ContextItem -> PromptBuilder -> RenderedPrompt
RenderedPrompt + LocalLLMAdapter -> LocalLLMResponse -> InferenceTrace
```

The prompt trace layer does not call a model by itself. It records what would be sent to an adapter and what the adapter returned. This prepares future local LLM experiments without making prompt/output data opaque.

See [Prompting and inference traces](prompting.md).

## Inference Review Layer

`InferenceReview` can attach human status, rating, flags, notes, and corrected response text to an `InferenceTrace`. `InferenceReviewPolicy` then makes deterministic eligibility decisions for future candidate use.

This keeps baseline traces from becoming training data, benchmark references, or knowledge seed candidates by accident. It is not an LLM judge and does not claim that a baseline answer is correct. See [Inference review foundation](inference-review.md).

## Running The Static Demo

```bash
python -m grona --local-llm-static-demo
python examples/local_llm_baseline_demo.py
python -m grona --prompt-trace-demo
python examples/prompt_trace_demo.py
python -m grona --inference-review-demo
python examples/inference_review_demo.py
```

All commands use deterministic static adapters or static traces only. They are deterministic and offline.

## Experiment Mode

`ExperimentRunner` supports `local_llm_baseline` as an explicit experiment mode. It requires a caller-provided `local_llm_adapter`.

If no adapter is provided, the runner raises a clear error instead of silently falling back to a hidden model call.

## Optional LM Studio-Compatible Adapter

`LMStudioCompletionAdapter` is available as a small foundation for future local experiments. It is not used by default, not used by CI, and not called by the static demos.

A caller must explicitly construct the adapter with a local base URL and then pass it into the baseline flow. The adapter parses OpenAI-style chat completion responses and returns visible error records when a request fails.

## Current Limits

- no streaming
- no tool calls
- no automatic prompt optimization
- no quality judging
- no answer superiority claims
- no persisted baseline result store
- no automatic conversion of inference traces into training examples
- no automatic conversion of inference reviews into training examples
- no default LM Studio call
- no external API integration by default

These limits keep the layer useful as a comparison contract without turning the prototype into a hidden model-calling application.
