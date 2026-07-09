@echo off
REM AutoMol Independent Installation Script for Windows
REM This script installs AutoMol as a standalone package using uv

setlocal enabledelayedexpansion

REM Colors (limited support in Windows)
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

REM Default values
set "ENV_NAME=%~1"
if "%ENV_NAME%"=="" set "ENV_NAME=.venv"

set "PYTHON_VER=%~2"
if "%PYTHON_VER%"=="" set "PYTHON_VER=3.12"

echo %GREEN%[%date% %time%] Starting AutoMol independent installation...%NC%
echo ================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR] Python is required but not installed. Please install Python 3.8+ first.%NC%
    echo Visit: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo %BLUE%[INFO] Found Python version: %PYTHON_VERSION%%NC%

REM Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[WARNING] uv package manager not found. Installing uv...%NC%
    
    REM Try to install uv using pip
    python -m pip install uv
    
    REM Verify installation
    uv --version >nul 2>&1
    if errorlevel 1 (
        echo %RED%[ERROR] Failed to install uv. Please install manually:%NC%
        echo Visit: https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
) else (
    echo %GREEN%[INFO] Found uv package manager%NC%
)

REM Create virtual environment
echo %GREEN%[INFO] Creating virtual environment '%ENV_NAME%' with Python %PYTHON_VER%...%NC%
uv venv "%ENV_NAME%" --python "%PYTHON_VER%"
if errorlevel 1 (
    echo %RED%[ERROR] Failed to create virtual environment%NC%
    pause
    exit /b 1
)

REM Activate virtual environment
echo %GREEN%[INFO] Activating virtual environment...%NC%
call "%ENV_NAME%\Scripts\activate.bat"

REM Check for wkhtmltopdf
where wkhtmltopdf >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[WARNING] wkhtmltopdf not found in PATH%NC%
    echo %YELLOW%[WARNING] Please install wkhtmltopdf manually for PDF generation:%NC%
    echo %YELLOW%[WARNING] https://wkhtmltopdf.org/downloads.html%NC%
)

REM Install AutoMol packages
echo %GREEN%[INFO] Installing AutoMol resources...%NC%
uv pip install -e automol_resources/
if errorlevel 1 (
    echo %RED%[ERROR] Failed to install AutoMol resources%NC%
    pause
    exit /b 1
)

echo %GREEN%[INFO] Installing AutoMol core package...%NC%
uv pip install -e automol/
if errorlevel 1 (
    echo %RED%[ERROR] Failed to install AutoMol core%NC%
    pause
    exit /b 1
)

REM Install additional recommended packages
echo %GREEN%[INFO] Installing additional dependencies...%NC%
uv pip install -r requirements.txt
uv pip install PyTDC
uv pip install rdkit==2024.3.5

REM Verify installation
echo %GREEN%[INFO] Verifying AutoMol installation...%NC%
python -c "
import sys
try:
    from automol.feature_generators import BottleneckTransformer
    print('+ AutoMol core package imported successfully')
    
    # Test encoder creation
    encoder = BottleneckTransformer(model='CHEMBL', use_gpu=False, batch_size=5)
    print('+ BottleneckTransformer created successfully')
    print('+ AutoMol installation verified!')
    
except ImportError as e:
    print('- AutoMol import failed:', e)
    sys.exit(1)
except Exception as e:
    print('- AutoMol verification failed:', e)
    sys.exit(1)
"
if errorlevel 1 (
    echo %RED%[ERROR] AutoMol verification failed%NC%
    pause
    exit /b 1
)

REM Success message
echo.
echo %GREEN%[SUCCESS] AutoMol installation completed successfully!%NC%
echo.
echo %BLUE%Environment name: %ENV_NAME%%NC%
echo %BLUE%Python version: %PYTHON_VER%%NC%
echo.
echo %BLUE%To use AutoMol:%NC%
echo %BLUE%1. Activate environment: %ENV_NAME%\Scripts\activate.bat%NC%
echo %BLUE%2. Try tutorials in the Tutorials\ folder%NC%
echo.
echo %BLUE%For Streamlit app: uv run streamlit run streamlit_app\automol_app.py%NC%
echo.
echo %GREEN%AutoMol is ready to use!%NC%
pause
