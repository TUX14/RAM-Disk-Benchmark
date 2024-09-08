@echo off
echo Preparing your system for RAM-Disk-Benchmark...

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed. Please install Python 3.x from https://www.python.org/
    exit /b 1
)

:: Check if pip is installed
where pip >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Pip is not installed. Please ensure pip is installed with Python.
    exit /b 1
)

:: Clone the repository
echo Cloning the repository...
git clone https://github.com/TUX14/RAM-Disk-Benchmark.git

:: Navigate to the project directory
cd RAM-Disk-Benchmark

:: Install dependencies
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found. Please check the repository.
)

echo Setup complete. You can now run the application by executing python app.py
pause
