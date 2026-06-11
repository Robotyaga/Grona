$ErrorActionPreference = "Stop"

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ToolsDir
Set-Location $RepoRoot

. (Join-Path $ToolsDir "local_training_env.ps1")

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $RepoRoot "logs\train_ultimate_lora_$Timestamp.log"
$TrainPython = Join-Path $RepoRoot ".venv-train\Scripts\python.exe"
$DatasetPath = Join-Path $RepoRoot "data\ultimate_grona_mix_001.jsonl"
$OutputDir = Join-Path $RepoRoot "outputs\qwen25-coder-3b-grona-ultimate-001"
$Confirmation = "I_UNDERSTAND_THIS_RUNS_LOCAL_TRAINING"

if (-not (Test-Path $TrainPython)) {
    throw "Training Python not found: $TrainPython"
}

if (-not (Test-Path $DatasetPath)) {
    throw "Dataset not found. Run .\grona.ps1 build-ultimate-dataset first: $DatasetPath"
}

function Invoke-LoggedCommand {
    param(
        [string]$Title,
        [string[]]$ArgsList
    )

    "==> $Title" | Tee-Object -FilePath $LogPath -Append
    & $TrainPython @ArgsList 2>&1 | Tee-Object -FilePath $LogPath -Append
    if ($LASTEXITCODE -ne 0) {
        throw "$Title failed with exit code $LASTEXITCODE"
    }
}

"Grona ultimate LoRA training $Timestamp" | Tee-Object -FilePath $LogPath
"Repo root: $RepoRoot" | Tee-Object -FilePath $LogPath -Append
"Dataset: $DatasetPath" | Tee-Object -FilePath $LogPath -Append
"Output: $OutputDir" | Tee-Object -FilePath $LogPath -Append

Invoke-LoggedCommand "train_lora_local.py" @(
    "tools\train_lora_local.py",
    "--model-id", "Qwen/Qwen2.5-Coder-3B-Instruct",
    "--dataset-path", $DatasetPath,
    "--output-dir", $OutputDir,
    "--max-steps", "4000",
    "--max-rows", "20000",
    "--batch-size", "2",
    "--grad-accum", "8",
    "--learning-rate", "1e-5",
    "--sequence-length", "256",
    "--allow-model-download",
    "--overwrite-output",
    "--confirmation-token", $Confirmation
)

"Training completed successfully." | Tee-Object -FilePath $LogPath -Append
Write-Host "Log: $LogPath"
