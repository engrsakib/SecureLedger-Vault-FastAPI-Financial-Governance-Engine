# Run tests from the project root: .\pytest.ps1
# Or after setup: .\.venv\Scripts\Activate.ps1  then  pytest

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPytest = Join-Path $ProjectRoot ".venv\Scripts\pytest.exe"

Set-Location $ProjectRoot

if (Test-Path $VenvPytest) {
    & $VenvPytest @PytestArgs
    exit $LASTEXITCODE
}

python -m pytest @PytestArgs
exit $LASTEXITCODE
