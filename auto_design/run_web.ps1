param([int]$Port = 8767, [string]$Workspace = (Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference = 'Stop'
$PythonCommand = if ($env:AUTODESIGN_PYTHON) { $env:AUTODESIGN_PYTHON } else { 'python3' }
& $PythonCommand "$PSScriptRoot/web/serve.py" --port $Port --workspace $Workspace
exit $LASTEXITCODE
