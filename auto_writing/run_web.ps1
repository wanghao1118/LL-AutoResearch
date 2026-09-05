param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8766,
    [switch]$Detached
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$candidates = @()
if ($env:CODEX_PYTHON) {
    $candidates += $env:CODEX_PYTHON
}
$runtimeRoot = Join-Path $env:USERPROFILE ".cache\codex-runtimes"
if (Test-Path -LiteralPath $runtimeRoot) {
    $candidates += Get-ChildItem -LiteralPath $runtimeRoot -Recurse -Filter "python.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like "*\dependencies\python\python.exe" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -ExpandProperty FullName
}
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    $candidates += $pythonCommand.Source
}

$python = $null
foreach ($candidate in $candidates | Select-Object -Unique) {
    if (-not (Test-Path -LiteralPath $candidate)) { continue }
    & $candidate --version *> $null
    if ($LASTEXITCODE -eq 0) {
        $python = $candidate
        break
    }
}
if (-not $python) {
    throw "A working Python 3 runtime was not found. Set CODEX_PYTHON and retry."
}

$serverScript = Join-Path $root "web\serve.py"
if ($Detached) {
    $logDirectory = Join-Path $root "tmp"
    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
    $stdout = Join-Path $logDirectory "web_server.stdout.log"
    $stderr = Join-Path $logDirectory "web_server.stderr.log"
    $arguments = @("-u", "`"$serverScript`"", "--host", $HostAddress, "--port", "$Port")
    $process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory (Split-Path -Parent $root) -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    Write-Host "Auto Writing started in the background (PID $($process.Id))."
    Write-Host "Open http://${HostAddress}:$Port"
    Write-Host "Logs: $stdout and $stderr"
    return
}

& $python $serverScript --host $HostAddress --port $Port
