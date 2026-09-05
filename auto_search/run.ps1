$ErrorActionPreference = "Stop"

$w2cCandidates = @()
if ($env:W2C_PYTHON) {
    $w2cCandidates += $env:W2C_PYTHON
}
$w2cCandidates += Get-ChildItem `
    -LiteralPath "$env:USERPROFILE\.cache\codex-runtimes" `
    -Recurse `
    -Filter "python.exe" `
    -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -ExpandProperty FullName

$w2cPython = $null
foreach ($w2cCandidate in $w2cCandidates) {
    if (-not (Test-Path -LiteralPath $w2cCandidate)) {
        continue
    }
    & $w2cCandidate --version *> $null
    if ($LASTEXITCODE -eq 0) {
        $w2cPython = $w2cCandidate
        break
    }
}

if (-not $w2cPython) {
    throw "No working Python runtime was found. Set W2C_PYTHON to python.exe."
}

if ($args.Count -eq 1 -and $args[0] -eq "--test") {
    & $w2cPython -m unittest discover -s (Join-Path $PSScriptRoot "tests") -v
    exit $LASTEXITCODE
}

if ($args.Count -ge 1 -and $args[0] -eq "--pipeline") {
    $w2cPipelineArgs = @($args | Select-Object -Skip 1)
    & $w2cPython (Join-Path $PSScriptRoot "research_pipeline.py") @w2cPipelineArgs
    exit $LASTEXITCODE
}

& $w2cPython (Join-Path $PSScriptRoot "generate_idea.py") @args
exit $LASTEXITCODE
