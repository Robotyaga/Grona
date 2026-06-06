# ruff: noqa: F401
"""Grona: sparse modular AI routing experiments."""

from .adapters import (
    ExecutionAdapter,
    ExecutionAdapterRegistry,
    ExecutionRequest,
    NoopExecutionAdapter,
    PythonFunctionAdapter,
    StaticExecutionAdapter,
    create_default_adapter_registry,
)
from .adaptive import AdaptiveRoutingConfig, ModuleFeedbackStats, build_module_feedback_stats
from .benchmark_runs import (
    BenchmarkRegressionReport,
    BenchmarkRunRecord,
    BenchmarkRunStore,
    InMemoryBenchmarkRunStore,
    JsonlBenchmarkRunStore,
    benchmark_report_from_dict,
    benchmark_report_to_dict,
    benchmark_result_from_dict,
    benchmark_result_to_dict,
    compare_benchmark_runs,
    create_benchmark_run_record,
)
from .benchmarks import (
    BenchmarkCase,
    BenchmarkReport,
    BenchmarkResult,
    BenchmarkRunConfig,
    BenchmarkSuite,
    create_demo_benchmark_cases,
    create_demo_benchmark_configs,
    domain_match_score,
    growth_decision_score,
    keyword_context_score,
    module_match_score,
    overall_benchmark_score,
    routing_match_score,
)
from .context import ContextBuilder, ContextItem
from .dataset_manifest import (
    DatasetIngestionReport,
    DatasetIngestor,
    DatasetLicensePolicy,
    DatasetManifest,
    JsonlDatasetRecord,
    read_jsonl_file,
    read_jsonl_records,
    read_jsonl_stream,
)
from .dataset_review import (
    DatasetQualityReviewer,
    DatasetReviewConfig,
    DatasetReviewReport,
    DatasetSampleReview,
    accepted_reviewed_samples_to_knowledge_seeds,
    review_ingested_samples,
)
from .datasets import (
    AlpacaFormatAdapter,
    ConversationDatasetSample,
    DatasetSample,
    DatasetSource,
    InstructionDatasetSample,
    ShareGPTFormatAdapter,
    create_demo_alpaca_samples,
    create_demo_dataset_sources,
    create_demo_sharegpt_samples,
    knowledge_seed_from_dataset_sample,
    knowledge_seeds_from_dataset_samples,
)
from .decision import ModuleMatch, RoutingDecision
from .defaults import create_default_registry
from .documents import (
    DocumentChunk,
    DocumentIngestor,
    DocumentSource,
    TextChunker,
    assign_domains,
    create_demo_document_sources,
    extract_keywords,
)
from .donor import (
    DonorModelAdapter,
    DonorModelError,
    DonorModelProposal,
    DonorProposalBatch,
    DonorProposalCollector,
    DonorProposalError,
    LMStudioAdapter,
    StaticDonorModelAdapter,
    knowledge_seed_from_donor_proposal,
)
from .executor import (
    AutomotiveDiagnosticsExpertExecutor,
    CodeExpertExecutor,
    CybersecurityExpertExecutor,
    DocumentSearchExpertExecutor,
    ExecutableExpert,
    ExpertExecutorRegistry,
    ExpertResult,
    GeneralReasoningExpertExecutor,
    MediaWorkflowExpertExecutor,
    create_default_executor_registry,
)
from .experiments import (
    EXPERIMENT_GATE_METRICS,
    EXPERIMENT_GATE_STATUSES,
    EXPERIMENT_MODES,
    ExperimentComparisonReport,
    ExperimentConfig,
    ExperimentGateConfig,
    ExperimentGateDecision,
    ExperimentRegressionGate,
    ExperimentResult,
    ExperimentRunner,
    MonolithBaseline,
    best_experiment_result,
    create_demo_experiment_configs,
)
from .feedback import (
    FeedbackRecord,
    FeedbackStore,
    FeedbackSummary,
    InMemoryFeedbackStore,
    JsonlFeedbackStore,
    summarize_feedback,
)
from .growth import (
    KnowledgeSeed,
    KnowledgeSource,
    KnowledgeValidator,
    ValidationResult,
    create_demo_knowledge_seeds,
    create_demo_knowledge_sources,
    knowledge_seed_from_document_chunk,
    knowledge_seed_from_tool_result,
)
from .growth_clusters import (
    GrapeAssignment,
    GrapeCluster,
    GrapeClusterer,
    GrapeNode,
    create_demo_grape_clusters,
    create_demo_grape_knowledge_seeds,
    create_demo_grape_nodes,
    memory_records_from_grape_clusters,
)
from .growth_engine import (
    GrowthDecision,
    GrowthEngine,
    GrowthEngineConfig,
    GrowthPlan,
    create_demo_growth_plan,
    create_growth_engine_demo_seeds,
    memory_records_from_growth_plan,
)
from .growth_review import (
    ConflictCheckResult,
    DuplicateCheckResult,
    KnowledgeConflictDetector,
    KnowledgeDeduplicator,
    KnowledgeReviewPipeline,
    NormalizedKnowledge,
    SeedReviewDecision,
    create_demo_review_knowledge_seeds,
)
from .inference_review import (
    InferenceReview,
    InferenceReviewConfig,
    InferenceReviewDecision,
    InferenceReviewPolicy,
    InferenceReviewSummary,
    InMemoryInferenceReviewStore,
    JsonlInferenceReviewStore,
)
from .local_llm import (
    LOCAL_LLM_STATIC_MODES,
    LMStudioCompletionAdapter,
    LocalLLMAdapter,
    LocalLLMBaselineResult,
    LocalLLMBaselineRunner,
    LocalLLMRequest,
    LocalLLMResponse,
    StaticLocalLLMAdapter,
    parse_chat_completion_text,
    static_local_llm_text,
)
from .memory import (
    InMemoryKeywordMemory,
    JsonlMemoryStore,
    MemoryModule,
    MemoryRecord,
    create_default_memory_modules,
)
from .module import ExpertModule
from .orchestrator import OrchestrationResult, Orchestrator
from .prompting import (
    InferenceTrace,
    InferenceTraceStore,
    InMemoryInferenceTraceStore,
    JsonlInferenceTraceStore,
    PromptBuilder,
    PromptTemplate,
    PromptTraceResult,
    RenderedPrompt,
    default_prompt_templates,
    get_default_prompt_template,
    run_prompt_trace,
    run_static_prompt_trace,
)
from .registry import ModuleRegistry
from .reviewed_trace_training import (
    ReviewedTraceBuildResult,
    ReviewedTraceTrainingExampleBuilder,
    build_training_examples_from_reviews,
    skipped_reviewed_trace_results,
    training_examples_from_build_results,
)
from .router import Router
from .safety import (
    ExecutionPlan,
    PolicyDecision,
    SafeExecutionAdapter,
    SafetyPolicy,
    ToolAction,
    create_default_safety_policy,
)
from .tools import (
    MockToolAdapter,
    SafeToolRunner,
    ToolAdapter,
    ToolRegistry,
    ToolRequest,
    ToolResult,
    ToolSpec,
    create_default_tool_registry,
)
from .training import (
    TrainingDataExporter,
    TrainingDataset,
    TrainingExample,
    TrainingExportConfig,
)
from .training_package import (
    DatasetCardDraft,
    TrainingDatasetPackage,
    TrainingDatasetSplit,
    TrainingDatasetSplitter,
    TrainingExportManifest,
    TrainingSplitConfig,
    build_training_dataset_package,
)
from .training_plan import (
    AdapterTrainingSpec,
    BaseModelSpec,
    ModelCardDraft,
    TrainingPlan,
    TrainingRunConfig,
    TrainingRunValidationResult,
    TrainingRunValidator,
    build_demo_training_plan,
)
from .workspace import (
    WorkspaceConfig,
    WorkspaceProfile,
    create_automotive_workspace_profile,
    create_code_assistant_workspace_profile,
    create_cybersecurity_workspace_profile,
    create_default_workspace_profile,
    create_document_research_workspace_profile,
    create_media_workflow_workspace_profile,
    filter_modules_for_workspace,
    get_builtin_workspace_profile,
)
