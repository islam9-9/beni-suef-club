$ErrorActionPreference = 'Stop'
$clubRuntime = (Get-Content (Join-Path $PSScriptRoot 'runtime.json') | ConvertFrom-Json).runtime
$clubListeners = Get-NetTCPConnection -LocalPort 8095 -State Listen -ErrorAction SilentlyContinue
foreach ($clubListener in $clubListeners) {
    $clubServerProcess = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $clubListener.OwningProcess)
    if ($clubServerProcess.CommandLine -notlike ('*' + $clubRuntime + '*')) { throw 'Unexpected service on port 8095; not stopping it.' }
    Stop-Process -Id $clubListener.OwningProcess
}
Write-Host 'Club Odoo stopped. Private PostgreSQL remains running for backup.'
