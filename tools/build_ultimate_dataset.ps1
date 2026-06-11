$ErrorActionPreference = "Stop"

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ToolsDir
Set-Location $RepoRoot

. (Join-Path $ToolsDir "local_training_env.ps1")

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $RepoRoot "logs\build_ultimate_dataset_$Timestamp.log"
$OutputPath = Join-Path $RepoRoot "data\ultimate_grona_mix_001.jsonl"
$TrainPython = Join-Path $RepoRoot ".venv-train\Scripts\python.exe"

if (-not (Test-Path $TrainPython)) {
    throw "Training Python not found: $TrainPython"
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

"Grona ultimate dataset build $Timestamp" | Tee-Object -FilePath $LogPath
"Repo root: $RepoRoot" | Tee-Object -FilePath $LogPath -Append
"Output: $OutputPath" | Tee-Object -FilePath $LogPath -Append

Invoke-LoggedCommand "make_big_hf_mix_dataset.py" @(
    "tools\make_big_hf_mix_dataset.py",
    "--output-jsonl",
    $OutputPath
)

if (-not (Test-Path $OutputPath)) {
    throw "Expected dataset was not created: $OutputPath"
}

$RowCount = (Get-Content -LiteralPath $OutputPath | Measure-Object -Line).Lines
"Rows: $RowCount" | Tee-Object -FilePath $LogPath -Append
if ($RowCount -le 100) {
    throw "Dataset row count must be > 100, got $RowCount"
}

"Dataset build completed successfully." | Tee-Object -FilePath $LogPath -Append
Write-Host "Log: $LogPath"
