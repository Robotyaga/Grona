$ErrorActionPreference = "Stop"

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ToolsDir
$CacheRoot = "F:\Grona\hf-cache"

$env:HF_HOME = $CacheRoot
$env:HF_HUB_CACHE = Join-Path $CacheRoot "hub"
$env:HF_DATASETS_CACHE = Join-Path $CacheRoot "datasets"
$env:TRANSFORMERS_CACHE = Join-Path $CacheRoot "transformers"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

$RepoDataDir = Join-Path $RepoRoot "data"
$RepoOutputsDir = Join-Path $RepoRoot "outputs"
$RepoLogsDir = Join-Path $RepoRoot "logs"

$Directories = @(
    $RepoDataDir,
    $RepoOutputsDir,
    $RepoLogsDir,
    $env:HF_HOME,
    $env:HF_HUB_CACHE,
    $env:HF_DATASETS_CACHE,
    $env:TRANSFORMERS_CACHE
)

foreach ($Directory in $Directories) {
    New-Item -ItemType Directory -Force -Path $Directory | Out-Null
}

Write-Host "Grona local training environment"
Write-Host "Repo root:          $RepoRoot"
Write-Host "Data dir:           $RepoDataDir"
Write-Host "Outputs dir:        $RepoOutputsDir"
Write-Host "Logs dir:           $RepoLogsDir"
Write-Host "HF_HOME:            $env:HF_HOME"
Write-Host "HF_HUB_CACHE:       $env:HF_HUB_CACHE"
Write-Host "HF_DATASETS_CACHE:  $env:HF_DATASETS_CACHE"
Write-Host "TRANSFORMERS_CACHE: $env:TRANSFORMERS_CACHE"
Write-Host "Downloads:          none"
