[CmdletBinding()]
param(
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$composeFile = 'docker/docker-compose.factoryops.yml'
$requiredServices = @('mysql', 'redis', 'rabbitmq', 'neo4j', 'qdrant', 'business-service', 'agent-service', 'frontend')

function Test-DockerEngine {
    try {
        docker version --format '{{.Server.Version}}' 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Wait-ForHealthyService([string]$service) {
    $deadline = (Get-Date).AddMinutes(4)
    do {
        $containerId = docker compose -f $composeFile ps -q $service
        if ($containerId) {
            $health = docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $containerId
            if ($health -eq 'healthy') { return }
        }
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $deadline)
    throw "服务 $service 未能在 4 分钟内变为健康状态。请运行：docker compose -f $composeFile logs $service"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw '未找到 Docker 命令。请安装 Docker Desktop 后重试。'
}

if (-not (Test-DockerEngine)) {
    $dockerDesktop = @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "$env:LocalAppData\Programs\DockerDesktop\Docker Desktop.exe",
        "$env:LocalAppData\Docker\Docker Desktop.exe"
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $dockerDesktop) {
        throw 'Docker 引擎未运行，且未找到 Docker Desktop。请安装并启动 Docker Desktop 后重试。'
    }
    Write-Host '正在启动 Docker Desktop…' -ForegroundColor Cyan
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    $deadline = (Get-Date).AddMinutes(2)
    while ((Get-Date) -lt $deadline -and -not (Test-DockerEngine)) { Start-Sleep -Seconds 3 }
    if (-not (Test-DockerEngine)) { throw 'Docker Desktop 未能在 2 分钟内启动 Docker 引擎。' }
}

Write-Host '正在构建并启动 SupplyGuard AI 服务…' -ForegroundColor Cyan
docker compose -f $composeFile up --build --detach
if ($LASTEXITCODE -ne 0) { throw 'Compose 启动失败。' }

Write-Host '正在等待服务健康检查…' -ForegroundColor Cyan
foreach ($service in $requiredServices) { Wait-ForHealthyService $service }

Write-Host ''
Write-Host 'SupplyGuard AI 已启动。' -ForegroundColor Green
Write-Host '前端：http://localhost:3000'
Write-Host '业务 API：http://localhost:8081/actuator/health'
Write-Host 'Agent API：http://localhost:8082/health'
Write-Host "停止命令：docker compose -f $composeFile down"

if (-not $NoBrowser) { Start-Process 'http://localhost:3000' }
