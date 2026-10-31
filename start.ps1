# Sets up the backend on first run, then starts the API.
# Dependencies are only installed when requirements.txt has changed.

$backendDir = Join-Path $PSScriptRoot "backend"
$venvDir = Join-Path $backendDir "venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$requirementsFile = Join-Path $backendDir "requirements.txt"
$installedFile = Join-Path $venvDir "installed-requirements.txt"
$pythonScript = Join-Path $backendDir "main.py"

function Stop-WithError($message) {
    Write-Host "ERROR: $message" -ForegroundColor Red
    exit 1
}

if (-Not (Test-Path $requirementsFile)) {
    Stop-WithError "Could not find $requirementsFile."
}

# Check if the virtual environment exists
if (-Not (Test-Path $venvPython)) {
    $pythonCommand = $null
    foreach ($candidate in "python", "py") {
        cmd /c "$candidate --version >nul 2>&1"
        if ($LASTEXITCODE -eq 0) {
            $pythonCommand = $candidate
            break
        }
    }
    if (-Not $pythonCommand) {
        Stop-WithError "Python was not found. Install Python 3 from https://www.python.org/downloads/ and try again."
    }

    Write-Host "Virtual environment not found. Creating..."
    & $pythonCommand -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "Could not create the virtual environment."
    }
}

# Install requirements if they are missing or out of date
$upToDate = (Test-Path $installedFile) -and
    ((Get-FileHash $requirementsFile).Hash -eq (Get-FileHash $installedFile).Hash)

if (-Not $upToDate) {
    Write-Host "Installing python dependencies..."
    & $venvPython -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "Could not install the dependencies. Check your internet connection and try again."
    }
    Copy-Item $requirementsFile $installedFile -Force
}

Write-Host "Starting the API at http://127.0.0.1:8000. Open frontend\index.html in your browser, and press Ctrl+C to stop."
& $venvPython $pythonScript
