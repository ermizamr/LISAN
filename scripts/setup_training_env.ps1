# ==============================================================================
# LISAN AI: Automated GPU Training Environment Setup (Windows PowerShell)
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\setup_training_env.ps1
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       LISAN AI - GPU TRAINING ENVIRONMENT SETUP            " -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Green
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "ERROR: Python is not found on PATH. Please install Python 3.10 or 3.11 from python.org." -ForegroundColor Red
    exit 1
}
$pythonVersion = python --version
Write-Host "  -> Found $pythonVersion" -ForegroundColor Gray

# 2. Check NVIDIA GPU via nvidia-smi
Write-Host "`n[2/6] Checking NVIDIA GPU hardware..." -ForegroundColor Green
$nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidiaSmi) {
    $gpuInfo = nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    Write-Host "  -> NVIDIA GPU Detected: $gpuInfo" -ForegroundColor Cyan
} else {
    Write-Host "  -> WARNING: nvidia-smi not found. Ensure NVIDIA Graphics Driver is installed." -ForegroundColor Yellow
}

# 3. Create Virtual Environment
Write-Host "`n[3/6] Setting up virtual environment (.venv)..." -ForegroundColor Green
if (-not (Test-Path ".venv")) {
    Write-Host "  -> Creating new virtual environment at .venv..." -ForegroundColor Gray
    python -m venv .venv
} else {
    Write-Host "  -> Existing .venv directory found." -ForegroundColor Gray
}

# 4. Activate Virtual Environment
Write-Host "`n[4/6] Activating virtual environment..." -ForegroundColor Green
$activateScript = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "  -> Virtual environment activated." -ForegroundColor Gray
} else {
    Write-Host "ERROR: Activation script not found at $activateScript" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "`n[5/6] Upgrading pip, wheel, and setuptools..." -ForegroundColor Green
python -m pip install --upgrade pip setuptools wheel

# 5. Install PyTorch with CUDA 12.1 Wheels
Write-Host "`n[6/6] Installing PyTorch with CUDA 12.1 support & training packages..." -ForegroundColor Green
Write-Host "  -> Installing CUDA-enabled PyTorch (this may take a few minutes)..." -ForegroundColor Gray
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install requirements
Write-Host "  -> Installing training & optimization packages..." -ForegroundColor Gray
python -m pip install -r training_requirements.txt

# 6. Run GPU Health Check
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "       VERIFYING GPU ACCELERATION & TRAINING READINESS       " -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
python scripts\check_gpu_env.py

Write-Host "`nEnvironment setup complete! Virtual environment is ready." -ForegroundColor Green
Write-Host "To activate in future sessions, run:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1; `$env:PYTHONUTF8=1;" -ForegroundColor Yellow
