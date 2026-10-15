@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set PYTHONUTF8=1

echo ============================================================
echo        LISAN AI - GPU TRAINING ENVIRONMENT SETUP (CMD)
echo ============================================================

echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found on PATH. Please install Python 3.10 or 3.11.
    pause
    exit /b 1
)

echo.
echo [2/5] Checking NVIDIA GPU...
where nvidia-smi >nul 2>nul
if %errorlevel% equ 0 (
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
) else (
    echo WARNING: nvidia-smi not found. Please ensure NVIDIA drivers are installed.
)

echo.
echo [3/5] Setting up virtual environment...
if not exist .venv (
    echo Creating .venv...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo.
echo [4/5] Installing PyTorch with CUDA 12.1...
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo [5/5] Installing training dependencies...
python -m pip install -r training_requirements.txt

echo.
echo ============================================================
echo        RUNNING GPU VERIFICATION DIAGNOSTICS
echo ============================================================
python scripts\check_gpu_env.py

echo.
echo Setup completed! To start training, run:
echo   call .venv\Scripts\activate.bat
echo   python scripts\run_all_training.py
echo ============================================================
pause
