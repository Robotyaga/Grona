param(
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$VenvDir = Join-Path $RepoRoot ".venv"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$TrainVenvDir = Join-Path $RepoRoot ".venv-train"
$TrainPython = Join-Path $TrainVenvDir "Scripts\python.exe"
$LocalTrainingEnv = Join-Path $RepoRoot "tools\local_training_env.ps1"
$Model3B = "Qwen/Qwen2.5-Coder-3B-Instruct"
$DonorAdapterDir = Join-Path $RepoRoot "outputs\qwen25-coder-3b-grona-donor-mix-002\adapter"
$DonorTokenizerDir = Join-Path $RepoRoot "outputs\qwen25-coder-3b-grona-donor-mix-002\tokenizer"
$UltimateAdapterDir = Join-Path $RepoRoot "outputs\qwen25-coder-3b-grona-ultimate-001\adapter"
$UltimateTokenizerDir = Join-Path $RepoRoot "outputs\qwen25-coder-3b-grona-ultimate-001\tokenizer"
$LoadConfirmation = "I_UNDERSTAND_THIS_LOADS_LOCAL_MODEL"

function Write-Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Ensure-Venv {
    if (-not (Test-Path $Python)) {
        Write-Step "Creating repo-local .venv"
        $Created = $false

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3.11 -m venv $VenvDir
    if (Test-Path $Python) {
        $Created = $true
    }

    if (-not $Created) {
        py -3.12 -m venv $VenvDir
        if (Test-Path $Python) {
            $Created = $true
        }
    }
}

if (-not $Created) {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv $VenvDir
        if (Test-Path $Python) {
            $Created = $true
        }
    }
}

if (-not $Created) {
    throw "Failed to create .venv. Install Python 3.11/3.12 or add python.exe to PATH."
}
    }

    Write-Step "Installing Grona editable dev package"
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -e ".[dev]"
}

function Run-Cmd($Title, $ArgsList) {
    Write-Step $Title
    & $Python @ArgsList
    if ($LASTEXITCODE -ne 0) {
        throw "$Title failed with exit code $LASTEXITCODE"
    }
}

function Ensure-Train-Python {
    if (-not (Test-Path $TrainPython)) {
        throw "Training Python not found: $TrainPython"
    }
}

function Use-Local-Training-Env {
    if (-not (Test-Path $LocalTrainingEnv)) {
        throw "Local training env helper not found: $LocalTrainingEnv"
    }
    . $LocalTrainingEnv
}

function Run-Train-Python($Title, $ArgsList) {
    Ensure-Train-Python
    Use-Local-Training-Env
    Write-Step $Title
    & $TrainPython @ArgsList
    if ($LASTEXITCODE -ne 0) {
        throw "$Title failed with exit code $LASTEXITCODE"
    }
}

function Test-GronaFlag($Flag) {
    $HelpText = & $Python -m grona --help 2>&1 | Out-String
    return $HelpText.Contains($Flag)
}

function Run-GronaFlagIfAvailable($Title, $Flag) {
    if (Test-GronaFlag $Flag) {
        Run-Cmd $Title @("-m", "grona", $Flag)
    }
    else {
        Write-Host ""
        Write-Host "==> Skipping $Title" -ForegroundColor Yellow
        Write-Host "Flag $Flag is not available in this checkout." -ForegroundColor Yellow
    }
}

function Show-Status {
    Write-Step "Grona status"
    Write-Host "Repo root: $RepoRoot"
    Write-Host "Venv:      $VenvDir"
    Write-Host "Python:    $Python"

    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Host ""
        git branch --show-current
        git status --short
    }
}

function Run-Setup {
    Ensure-Venv
    Show-Status
}

function Run-Lint {
    Ensure-Venv
    Run-Cmd "ruff check ." @("-m", "ruff", "check", ".")
}

function Run-Test {
    Ensure-Venv
    Run-Cmd "pytest" @("-m", "pytest")
}

function Run-Demos {
    Ensure-Venv
    Run-GronaFlagIfAvailable "model build readiness demo" "--model-build-readiness-demo"
    Run-GronaFlagIfAvailable "training pipeline audit demo" "--training-pipeline-audit-demo"
    Run-GronaFlagIfAvailable "local trainer spike demo" "--local-trainer-spike-demo"
}

function Run-Train-Env {
    Use-Local-Training-Env
}

function Run-Build-Ultimate-Dataset {
    $Script = Join-Path $RepoRoot "tools\build_ultimate_dataset.ps1"
    & powershell -ExecutionPolicy Bypass -File $Script
    if ($LASTEXITCODE -ne 0) {
        throw "build-ultimate-dataset failed with exit code $LASTEXITCODE"
    }
}

function Run-Train-Ultimate {
    $Script = Join-Path $RepoRoot "tools\train_ultimate_lora.ps1"
    & powershell -ExecutionPolicy Bypass -File $Script
    if ($LASTEXITCODE -ne 0) {
        throw "train-ultimate failed with exit code $LASTEXITCODE"
    }
}

function Run-Chat-Adapter($Title, $AdapterDir, $TokenizerDir) {
    Run-Train-Python $Title @(
        "tools\chat_lora_adapter.py",
        "--model-id", $Model3B,
        "--adapter-dir", $AdapterDir,
        "--tokenizer-dir", $TokenizerDir,
        "--confirmation-token", $LoadConfirmation
    )
}

function Run-Eval-Adapter($Title, $AdapterDir, $TokenizerDir) {
    Run-Train-Python $Title @(
        "tools\eval_lora_adapter.py",
        "--model-id", $Model3B,
        "--adapter-dir", $AdapterDir,
        "--tokenizer-dir", $TokenizerDir,
        "--allow-model-download",
        "--confirmation-token", $LoadConfirmation
    )
}

function Run-Work {
    Ensure-Venv
    Run-GronaFlagIfAvailable "model build readiness demo" "--model-build-readiness-demo"
    Run-GronaFlagIfAvailable "local trainer spike demo" "--local-trainer-spike-demo"

    Write-Host ""
    Write-Host "Next commands:" -ForegroundColor Green
    Write-Host "  .\grona.ps1 check"
    Write-Host "  .\grona.ps1 lint"
    Write-Host "  .\grona.ps1 test"
    Write-Host "  .\grona.ps1 demos"
}

function Run-Check {
    Ensure-Venv

    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Step "git status"
        git status
        Write-Step "git fetch"
        git fetch
    }

    Run-Lint
    Run-Test
    Run-Demos

    Write-Host ""
    Write-Host "Grona check completed successfully." -ForegroundColor Green
}

function Show-Help {
    Write-Host "Grona portable launcher"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\grona.ps1 check"
    Write-Host "  .\grona.ps1 work"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  check   Full safe readiness check"
    Write-Host "  work    Lightweight working-mode readiness"
    Write-Host "  setup   Create/update repo-local .venv"
    Write-Host "  lint    Run ruff check ."
    Write-Host "  test    Run pytest"
    Write-Host "  demos   Run safe demo commands"
    Write-Host "  train-env                Prepare local training env/cache dirs"
    Write-Host "  build-ultimate-dataset   Build data/ultimate_grona_mix_001.jsonl"
    Write-Host "  train-ultimate           Train outputs/qwen25-coder-3b-grona-ultimate-001"
    Write-Host "  chat-3b-donor            Chat with donor 3B LoRA adapter"
    Write-Host "  chat-3b-ultimate         Chat with ultimate 3B LoRA adapter"
    Write-Host "  eval-3b-donor            Heuristic eval for donor 3B adapter"
    Write-Host "  eval-3b-ultimate         Heuristic eval for ultimate 3B adapter"
    Write-Host "  status  Show repo/venv/git status"
    Write-Host "  help    Show this help"
}

switch ($Command.ToLowerInvariant()) {
    "check"                  { Run-Check }
    "work"                   { Run-Work }
    "setup"                  { Run-Setup }
    "lint"                   { Run-Lint }
    "test"                   { Run-Test }
    "demos"                  { Run-Demos }
    "train-env"              { Run-Train-Env }
    "build-ultimate-dataset" { Run-Build-Ultimate-Dataset }
    "train-ultimate"         { Run-Train-Ultimate }
    "chat-3b-donor"          { Run-Chat-Adapter "chat donor 3B LoRA" $DonorAdapterDir $DonorTokenizerDir }
    "chat-3b-ultimate"       { Run-Chat-Adapter "chat ultimate 3B LoRA" $UltimateAdapterDir $UltimateTokenizerDir }
    "eval-3b-donor"          { Run-Eval-Adapter "eval donor 3B LoRA" $DonorAdapterDir $DonorTokenizerDir }
    "eval-3b-ultimate"       { Run-Eval-Adapter "eval ultimate 3B LoRA" $UltimateAdapterDir $UltimateTokenizerDir }
    "status"                 { Show-Status }
    "help"                   { Show-Help }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
