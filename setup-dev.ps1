# One-time dev setup: creates .venv and installs dependencies (including pytest)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Creating virtual environment in .venv ..."
python -m venv .venv

Write-Host "Installing dependencies ..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt

Write-Host ""
Write-Host "Done. Use tests with either:"
Write-Host "  1) .\.venv\Scripts\Activate.ps1   then   pytest"
Write-Host "  2) .\pytest.ps1"
Write-Host "  3) python -m pytest"
