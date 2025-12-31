@echo off
setlocal

:: Get the directory of the batch script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check for Python Executable
if exist "python.exe" (
    set "PYTHON_EXE=python.exe"
) else (
    echo Python executable not found in this folder.
    echo Please ensure this script is next to python.exe (Python Embedded).
    pause
    exit /b 1
)

:: Enable 'import site' in ._pth file to allow pip
:: Find the ._pth file (e.g., python311._pth)
for %%f in (*._pth) do (
    set "PTH_FILE=%%f"
)

if defined PTH_FILE (
    :: Check if "import site" is active (at start of line)
    findstr /B /C:"import site" "%PTH_FILE%" >nul
    if errorlevel 1 (
        echo Enabling 'import site' in %PTH_FILE%...
        echo.>> "%PTH_FILE%"
        echo import site>> "%PTH_FILE%"
    )
)

:: Check for PIP
if not exist "Lib\site-packages\pip" (
    echo PIP not found. Attempting to install...

    :: Check if get-pip.py exists
    if not exist "get-pip.py" (
        echo Downloading get-pip.py...
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    )

    echo Installing pip...
    %PYTHON_EXE% get-pip.py

    :: Clean up
    del get-pip.py
)

:: Install Dependencies
echo Checking dependencies...
%PYTHON_EXE% -m pip install -r requirements.txt --quiet

:: Run Application
echo Starting Application...
%PYTHON_EXE% main.py

endlocal
