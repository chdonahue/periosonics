@echo off
setlocal enabledelayedexpansion

echo Starting setup process...
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment!
    pause
    exit /b 1
)
echo Virtual environment created successfully.
echo.

REM Set execution policy
echo Setting execution policy...
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
if %errorlevel% neq 0 (
    echo Warning: Failed to set execution policy. This might not be a problem.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment!
    pause
    exit /b 1
)
echo Virtual environment activated successfully.
echo.

REM Install requirements
echo Installing required packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install required packages!
    deactivate
    pause
    exit /b 1
)
echo Packages installed successfully.
echo.

echo Setup completed successfully!
echo You can now close this window and start using the application.
pause