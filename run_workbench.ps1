param([int]$Port = 8760, [string]$Workspace = $PSScriptRoot)
$ErrorActionPreference = "Stop"
$workbenchPython = if ($env:AUTORESEARCH_PYTHON) { $env:AUTORESEARCH_PYTHON } else { "python3" }
Push-Location $PSScriptRoot
try { & $workbenchPython -m workbench --port $Port --workspace $Workspace; exit $LASTEXITCODE }
finally { Pop-Location }
