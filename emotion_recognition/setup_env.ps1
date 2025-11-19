<#
setup_env.ps1

Creates a Python virtual environment and installs packages from `requirements.txt`.

Usage (PowerShell):
  .\setup_env.ps1            # creates .venv and installs deps
  .\setup_env.ps1 -VenvPath ".venv"  # custom venv path

If you want to activate the venv in the current shell after running, run:
  .\.venv\Scripts\Activate.ps1
#>

param(
    [string]$VenvPath = ".venv",
    [switch]$NoInstall
)

Write-Host "Setting up Python virtual environment at: $VenvPath"

# Check python availability
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "Python not found. Install Python 3.8+ from https://www.python.org/ and ensure 'python' is on PATH."
    exit 1
}

if (-Not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment..."
    python -m venv $VenvPath
} else {
    Write-Host "Virtual environment already exists at $VenvPath"
}

Write-Host "Activating virtual environment for package installation..."
# Activate the venv for the current script scope
& "$VenvPath\Scripts\Activate.ps1"

Write-Host "Upgrading pip, setuptools, wheel..."
python -m pip install --upgrade pip setuptools wheel

if (-not $NoInstall) {
    if (-not (Test-Path "requirements.txt")) {
        Write-Warning "requirements.txt not found in current folder. Skipping package install."
    } else {
        Write-Host "Installing packages from requirements.txt (this may take several minutes)..."
        python -m pip install -r requirements.txt
    }
} else {
    Write-Host "Skipping package install because -NoInstall was passed."
}

Write-Host "Setup complete. To activate the venv in your interactive shell run:" -ForegroundColor Green
Write-Host "    .\$VenvPath\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "Then run the script, for example:" -ForegroundColor Green
Write-Host "    python .\script.py videos\your_video.mp4" -ForegroundColor Yellow
