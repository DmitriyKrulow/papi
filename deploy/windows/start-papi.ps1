<#
.SYNOPSIS
    Поднимает docker-стек PAPI. Запускается задачей планировщика при загрузке
    сервера, поэтому умеет ждать, пока поднимется сам Docker Desktop.

.DESCRIPTION
    Особенность Windows: в отличие от Linux, докер-демон там запускается не
    службой ядра, а приложением Docker Desktop. После перезагрузки сервера
    проходит от десятка секунд до пары минут, прежде чем появится именованный
    канал \\.\pipe\docker_engine и docker CLI начнёт отвечать.

    Поэтому скрипт:
      1) запускает Docker Desktop, если демон не отвечает;
      2) ждёт готовности демона (с таймаутом);
      3) выполняет docker compose up -d.

    Ручной запуск:
        powershell -NoProfile -ExecutionPolicy Bypass -File .\start-papi.ps1
#>
[CmdletBinding()]
param(
    [string]$ProjectDir = 'C:\papi',
    [string]$DockerDesktopExe = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = 'Continue'
$logDir = Join-Path $ProjectDir 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = Join-Path $logDir 'start.log'

function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

Write-Log '--- запуск PAPI ---'

if (-not (Test-Path (Join-Path $ProjectDir 'docker-compose.yml'))) {
    Write-Log "ОШИБКА: в $ProjectDir нет docker-compose.yml"
    exit 1
}

# --- Ждём (или поднимаем) докер-демон ----------------------------------------
function Test-DockerReady {
    # `docker info` возвращает код 2, если демон недоступен. Пробовать один раз
    # быстрее, чем гонять compose с его проверками.
    $null = docker version --format '{{.Server.Version}}' 2>$null
    return ($LASTEXITCODE -eq 0)
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$startedDesktop = $false

while ((Get-Date) -lt $deadline) {
    if (Test-DockerReady) {
        break
    }
    if (-not $startedDesktop) {
        if (Test-Path $DockerDesktopExe) {
            Write-Log 'Докер-демон не отвечает - запускаю Docker Desktop'
            Start-Process $DockerDesktopExe
            $startedDesktop = $true
        }
        else {
            Write-Log "Docker Desktop не найден по пути $DockerDesktopExe - жду запущенный демон"
            $startedDesktop = $true
        }
    }
    Start-Sleep -Seconds 5
}

if (-not (Test-DockerReady)) {
    Write-Log "ОШИБКА: докер-демон не поднялся за $TimeoutSeconds с. Пробую позже (задача повторится)."
    exit 1
}
Write-Log 'Докер-демон готов'

# --- Поднимаем стек ----------------------------------------------------------
Push-Location $ProjectDir
try {
    # up -d идемпотентен: контейнеры с актуальной конфигурацией не трогаются.
    # Политика restart: unless-stopped обычно поднимает их сама вместе с демоном;
    # этот вызов страхует случай, когда стек был остановлен через `compose down`.
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ОШИБКА: docker compose up завершился с кодом $LASTEXITCODE"
        exit $LASTEXITCODE
    }
    Write-Log 'Стек поднят'
    docker compose ps | ForEach-Object { Write-Log $_ }
}
finally {
    Pop-Location
}
