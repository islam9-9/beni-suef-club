$ErrorActionPreference = 'Stop'
$labRuntime = (Get-Content (Join-Path $PSScriptRoot 'runtime.json') | ConvertFrom-Json).runtime
$labSource = (Get-Content (Join-Path $labRuntime 'source.json') | ConvertFrom-Json).commit
if (Get-NetTCPConnection -LocalPort 8096 -State Listen -ErrorAction SilentlyContinue) {
    Write-Host 'Port 8096 already in use; no additional process started.'
    exit
}
$env:Path = (Join-Path $labRuntime 'frontend\node_modules\.bin') + ';C:\Users\accis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;C:\Program Files\Odoo 19.0e.20251117\thirdparty;' + $env:Path
$labArgs = '"' + (Join-Path $labRuntime ('odoo-' + $labSource + '\odoo-bin')) + '" -c "' + (Join-Path $labRuntime 'membership-lab.conf') + '"'
Start-Process -FilePath (Join-Path $labRuntime 'venv\Scripts\python.exe') -ArgumentList $labArgs -WindowStyle Hidden
Write-Host 'Membership test environment starting: http://127.0.0.1:8096'
