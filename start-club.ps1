$ErrorActionPreference = 'Stop'
$clubRuntime = (Get-Content (Join-Path $PSScriptRoot 'runtime.json') | ConvertFrom-Json).runtime
$clubSource = Get-Content (Join-Path $clubRuntime 'source.json') | ConvertFrom-Json
$clubServer = Join-Path $clubRuntime ('odoo-' + $clubSource.commit)
$clubPython = Join-Path $clubRuntime 'venv\Scripts\python.exe'
$clubNode = 'C:\Users\accis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin'
$env:Path = (Join-Path $clubRuntime 'frontend\node_modules\.bin') + ';' + $clubNode + ';C:\Program Files\Odoo 19.0e.20251117\thirdparty;' + $env:Path
if (-not (Get-NetTCPConnection -LocalPort 5495 -State Listen -ErrorAction SilentlyContinue)) {
    $clubPgArgs = '-D "' + (Join-Path $clubRuntime 'pgdata') + '" -l "' + (Join-Path $clubRuntime 'logs\postgres.log') + '" -w start'
    $clubPg = Start-Process -FilePath (Join-Path $clubRuntime 'pgsql\bin\pg_ctl.exe') -ArgumentList $clubPgArgs -WindowStyle Hidden -PassThru
    $clubPg.WaitForExit()
    if ($clubPg.ExitCode -ne 0) { throw 'Club PostgreSQL failed to start; check logs/postgres.log' }
}
if (Get-NetTCPConnection -LocalPort 8095 -State Listen -ErrorAction SilentlyContinue) {
    Write-Host 'Port 8095 is already listening. Club URL: http://127.0.0.1:8095'
    exit
}
$clubArguments = '"' + (Join-Path $clubServer 'odoo-bin') + '" -c "' + (Join-Path $clubRuntime 'odoo.conf') + '"'
$clubProcess = Start-Process -FilePath $clubPython -ArgumentList $clubArguments -WorkingDirectory $clubServer -WindowStyle Hidden -PassThru
$clubProcess.Id | Set-Content (Join-Path $clubRuntime 'server.pid')
Write-Host 'Club development server starting: http://127.0.0.1:8095'
