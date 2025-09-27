# Helper script to setup the project's Python environment.

# ---
# 1. Check if python is installed and available in PATH
# ---
$python_executable = Get-Command python -ErrorAction SilentlyContinue
if (-not $python_executable) {
    Write-Host "ERROR: python is not installed or not in PATH."
    Write-Host "Please install python 3.11 or newer from https://www.python.org/downloads/"
    Write-Host "IMPORTANT: During installation, make sure to check the box 'Add python.exe to PATH'"
    exit 1
}

# ---
# 2. Check python version
# ---
$python_version = & $python_executable -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
$python_version_major = $python_version.Split('.')[0]
$python_version_minor = $python_version.Split('.')[1]

if (($python_version_major -lt 3) -or ($python_version_major -eq 3 -and $python_version_minor -lt 11)) {
    Write-Host "ERROR: python version is $python_version, but >=3.11 is required."
    Write-Host "Please install python 3.11 or newer from https://www.python.org/downloads/"
    exit 1
}

Write-Host "Python version $python_version found."

# ---
# 3. Create a virtual environment
# ---
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    & $python_executable -m venv .venv
}

# ---
# 4. Install dependencies
# ---
Write-Host "Installing dependencies..."
& .\.venv\Scripts\python.exe -m pip install -e ".[all]"

Write-Host "Setup complete."
