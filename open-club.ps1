param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
try {
    & (Join-Path $PSScriptRoot 'start-club.ps1')
    $clubReady = $false
    $clubDeadline = (Get-Date).AddSeconds(90)
    do {
        try {
            $clubResponse = Invoke-WebRequest -Uri 'http://127.0.0.1:8095/web/login' -TimeoutSec 5
            $clubReady = $clubResponse.StatusCode -eq 200
        } catch { Start-Sleep -Seconds 2 }
    } until ($clubReady -or (Get-Date) -gt $clubDeadline)
    if (-not $clubReady) { throw 'Club did not become ready within 90 seconds.' }
    if (-not $CheckOnly) { Start-Process 'http://127.0.0.1:8095/web/login?db=beni_suef_club_dev' }
    Write-Host 'Club is ready: http://127.0.0.1:8095'
} catch {
    $clubRuntime = (Get-Content (Join-Path $PSScriptRoot 'runtime.json') | ConvertFrom-Json).runtime
    $clubErrorFile = Join-Path $clubRuntime 'startup-error.txt'
    "Could not start the club system. Share this error with support:`r`n$($_.Exception.Message)" | Set-Content $clubErrorFile -Encoding utf8
    if (-not $CheckOnly) { Start-Process notepad.exe -ArgumentList ('"' + $clubErrorFile + '"') }
    throw
}
