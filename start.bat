@echo off
setlocal

@REM Sets up the backend on first run, then starts the API.
@REM Dependencies are only installed when requirements.txt has changed.

cd /d "%~dp0backend"
if errorlevel 1 (
    echo ERROR: Could not find the backend folder.
    goto :fail
)

set "venvDir=venv"
set "venvPython=venv\Scripts\python.exe"
set "requirementsFile=requirements.txt"
set "installedFile=venv\installed-requirements.txt"
set "pythonScript=main.py"

if not exist "%requirementsFile%" (
    echo ERROR: Could not find backend\%requirementsFile%.
    goto :fail
)

if exist "%venvPython%" goto :install

set "pythonCommand="
python --version >nul 2>&1 && set "pythonCommand=python"
if not defined pythonCommand py --version >nul 2>&1 && set "pythonCommand=py"
if not defined pythonCommand (
    echo ERROR: Python was not found. Install Python 3 from https://www.python.org/downloads/ and try again.
    goto :fail
)

echo Virtual environment not found. Creating...
%pythonCommand% -m venv %venvDir%
if errorlevel 1 (
    echo ERROR: Could not create the virtual environment.
    goto :fail
)

:install
if exist "%installedFile%" fc /b "%requirementsFile%" "%installedFile%" >nul 2>&1 && goto :run

echo Installing python dependencies...
"%venvPython%" -m pip install -r %requirementsFile%
if errorlevel 1 (
    echo ERROR: Could not install the dependencies. Check your internet connection and try again.
    goto :fail
)
copy /y "%requirementsFile%" "%installedFile%" >nul

:run
echo Starting the API at http://127.0.0.1:8000. Open frontend\index.html in your browser, and press Ctrl+C to stop.
"%venvPython%" %pythonScript%
endlocal
exit /b

:fail
pause
endlocal
exit /b 1
