[CmdletBinding()]
param(
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$uiDirectory = Join-Path $repositoryRoot 'frontend'
$uiUrl = 'http://localhost:5173'

function Test-FactoryOpsDemo {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $uiUrl -TimeoutSec 3
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw 'Node.js/npm was not found. The FactoryOps demo cannot start.'
}

if (-not (Test-Path -LiteralPath (Join-Path $uiDirectory 'node_modules'))) {
    Write-Host 'Installing demo dependencies...' -ForegroundColor Cyan
    Push-Location $uiDirectory
    try { npm.cmd ci } finally { Pop-Location }
}

if (-not (Test-FactoryOpsDemo)) {
    Write-Host 'Starting the unified SupplyGuard AI workspace...' -ForegroundColor Cyan
    Start-Process -FilePath 'npm.cmd' -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173') -WorkingDirectory $uiDirectory -WindowStyle Hidden

    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline -and -not (Test-FactoryOpsDemo)) {
        Start-Sleep -Seconds 2
    }
}

if (-not (Test-FactoryOpsDemo)) {
    throw 'The unified SupplyGuard AI workspace did not start within 60 seconds.'
}

Write-Host 'The unified SupplyGuard AI workspace is running.' -ForegroundColor Green
Write-Host "URL: $uiUrl"
Write-Host 'Quality operations, supply-chain graph, and simulation are available from one homepage.'

if (-not $NoBrowser) { Start-Process $uiUrl }
