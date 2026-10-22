@echo off
setlocal
cd /d "%~dp0"
set "UV_CACHE_DIR=%CD%\.uv-cache"
set "UV_PYTHON_INSTALL_DIR=%CD%\.python"
set "PYTHONDONTWRITEBYTECODE=1"
where uv >nul 2>nul
if errorlevel 1 (
    echo uv was not found. See README.md for setup instructions.
    pause
    exit /b 1
)
uv python find --managed-python --no-python-downloads 3.12 >nul 2>nul
if errorlevel 1 (
    uv python install 3.12 --no-bin --no-registry
    if errorlevel 1 (
        echo Python setup did not finish. Check your connection and see README.md.
        pause
        exit /b 1
    )
)
uv run --no-project --managed-python --python 3.12 app.py %*
if errorlevel 1 (
    echo.
    echo The app could not start. Keep this message and see README.md.
    pause
    exit /b 1
)

