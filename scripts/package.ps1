param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

if ($Clean) {
    if (Test-Path build) {
        Remove-Item -Recurse -Force build
    }
    if (Test-Path dist) {
        Remove-Item -Recurse -Force dist
    }
}

if ($env:IMPROTHEATRE_PYTHON) {
    $python = $env:IMPROTHEATRE_PYTHON
}
else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Python executable not found. Set IMPROTHEATRE_PYTHON to the interpreter you want to package with."
    }
    $python = $pythonCommand.Source
}

& $python -m pip install -e ".[packaging]"
& $python -m PyInstaller --noconfirm ImproTheatre.spec

Write-Host "Packaged app available under dist/ImproTheatre/"