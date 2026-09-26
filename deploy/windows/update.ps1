<#
.SYNOPSIS
    Обновление PAPI из git-репозитория (Windows-аналог update.sh).

.DESCRIPTION
    Порядок такой же, как на Ubuntu:
      1. проверка, что .env на месте и содержит нужные ключи;
      2. проверка, что порты 80/8080 не заняты чужими процессами;
      3. дамп базы данных в backups\ перед обновлением;
      4. git fetch + git reset --hard origin\<branch>;
      5. пересборка образов и docker compose up -d;
      6. проверка доступности backend и frontend.

    Скрипт рассчитан и на ручной запуск, и на задачу планировщика PAPI-Update.
    Лог: <ProjectDir>\logs\update.log

.PARAMETER Branch
    Ветка обновления. По умолчанию main

.PARAMETER ProjectDir
    Каталог установки. По умолчанию C:\papi
#>
[CmdletBinding()]
param(
    [string]$Branch     = 'main',
    [string]$ProjectDir = 'C:\papi'
)

$ErrorActionPreference = 'Stop'

$envFile   = Join-Path $ProjectDir '.env'
$envExample= Join-Path $ProjectDir '.env.example'
$backupDir = Join-Path $ProjectDir 'backups'
$logDir    = Join-Path $ProjectDir 'logs'
$logFile   = Join-Path $logDir 'update.log'
$backupKeep = 10

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

function Get-EnvValue([string]$Name, [string]$Default) {
    if (-not (Test-Path $envFile)) { return $Default }
    $line = Select-String -Path $envFile -Pattern "^\s*$Name=" | Select-Object -Last 1
    if ($line) {
        $value = ($line.Line -split '=', 2)[1].Trim().Trim('"')
        if ($value) { return $value }
    }
    return $Default
}

Write-Log '=========================================='
Write-Log 'Начинаем обновление проекта PAPI'
Write-Log '=========================================='

# --- 1. .env -----------------------------------------------------------------
if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Log "$envFile создан из .env.example - заполните пароли и порты"
}

# Недостаток ключа в .env ломает compose на ${POSTGRES_USER:?...}, поэтому
# недостающие строки дописываем из шаблона (существующие не трогаем).
$exampleKeys = Select-String -Path $envExample -Pattern '^\s*([A-Za-z_][A-Za-z0-9_]*)=' |
    ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique
$added = 0
foreach ($key in $exampleKeys) {
    if (-not (Select-String -Path $envFile -Pattern "^\s*$key=" -Quiet)) {
        $line = Select-String -Path $envExample -Pattern "^\s*$key=" | Select-Object -First 1
        Add-Content -Path $envFile -Value $line.Line
        $added++
    }
}
if ($added -gt 0) {
    Write-Log "В .env добавлено недостающих ключей: $added (значения из шаблона - замените своими)"
}

$AppPort = Get-EnvValue 'APP_PORT' '80'
$ApiPort = Get-EnvValue 'API_PORT' '8080'
$DbUser  = Get-EnvValue 'POSTGRES_USER' ''
$DbName  = Get-EnvValue 'POSTGRES_DB' ''

# --- 2. Свободны ли порты ----------------------------------------------------
# Занятый порт приводит к "port is already allocated" при пересоздании контейнера.
foreach ($port in @($AppPort, $ApiPort)) {
    $owner = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
             Select-Object -First 1
    if (-not $owner) { continue }

    $ownerName = (Get-Process -Id $owner.OwningProcess -ErrorAction SilentlyContinue).ProcessName
    # Наши же контейнеры (winnat/com.docker.backend) - штатная ситуация:
    # compose пересоберёт привязку. Сигналом об проблеме считается чужой процесс.
    if ($ownerName -match 'docker|com\.docker|winnat|vpnkit') {
        Write-Log "Порт $port занят docker ($ownerName) - так и должно быть"
        continue
    }
    Write-Log "ОШИБКА: порт $port занят процессом '$ownerName' (PID $($owner.OwningProcess))"
    Write-Log 'Освободите порт или поменяйте его в .env'
    exit 1
}

# --- 3. Бэкап БД -------------------------------------------------------------
if (-not (Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir -Force | Out-Null }

$running = docker ps --format '{{.Names}}' 2>$null
if ($running -contains 'papi-db') {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $dumpPlain = Join-Path $backupDir "pre_update_$stamp.sql"
    # Дамп сначала в файл: в пайпе с gzip код возврата даёт последний элемент,
    # и оборванный дамп выглядел бы успешным.
    docker exec papi-db pg_dump -U $DbUser -d $DbName --file=/tmp/pre_update.sql 2>>$logFile
    if ($LASTEXITCODE -eq 0) {
        docker cp "papi-db:/tmp/pre_update.sql" $dumpPlain 2>>$logFile
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Бэкап БД перед обновлением: $dumpPlain"
            Get-ChildItem $backupDir -Filter 'pre_update_*.sql' |
                Sort-Object LastWriteTime -Descending |
                Select-Object -Skip $backupKeep |
                Remove-Item -Force -ErrorAction SilentlyContinue
        }
        docker exec papi-db rm -f /tmp/pre_update.sql 2>$null | Out-Null
    }
    if ($LASTEXITCODE -ne 0) {
        if (Test-Path $dumpPlain) { Remove-Item $dumpPlain -Force }
        Write-Log 'Не удалось снять дамп БД - продолжаем без него'
    }
}
else {
    Write-Log 'Контейнер papi-db не запущен - бэкап перед обновлением пропущен'
}

# --- 4. Обновление кода ------------------------------------------------------
Push-Location $ProjectDir
try {
    Write-Log "Обновляем код из git ($Branch)"
    # git считает каталог «подозрительным», если его клонировал другой
    # пользователь (например, установка шла от администратора).
    git config --global --add safe.directory ($ProjectDir -replace '\\', '/') 2>$null | Out-Null

    git fetch origin $Branch 2>>$logFile
    if ($LASTEXITCODE -ne 0) {
        Write-Log 'ОШИБКА: git fetch не выполнился (нет сети или доступ к репозиторию)'
        exit 1
    }
    # reset --hard вместо pull: в каталоге есть runtime-файлы (uploads, кэш,
    # node_modules), из-за которых pull падает с "would be overwritten by merge".
    # .env и backups в git не входят, поэтому они остаются на месте.
    git reset --hard "origin/$Branch" 2>>$logFile
    if ($LASTEXITCODE -ne 0) {
        Write-Log 'ОШИБКА: git reset --hard не выполнился'
        exit 1
    }
}
finally {
    Pop-Location
}

# --- 5. Сборка и запуск ------------------------------------------------------
Write-Log 'Пересобираем образы...'
Push-Location $ProjectDir
try {
    docker compose build --pull 2>&1 | Tee-Object -FilePath $logFile -Append
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Сборка образов завершилась с ошибкой (код $LASTEXITCODE) - контейнеры остались на предыдущем состоянии"
        exit 1
    }

    Write-Log 'Перезапускаем контейнеры...'
    docker compose up -d 2>&1 | Tee-Object -FilePath $logFile -Append
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Ошибка docker compose up (код $LASTEXITCODE)"
        exit 1
    }
}
finally {
    Pop-Location
}

# --- 6. Проверка работы ------------------------------------------------------
Write-Log 'Проверяем работу сервисов...'

function Test-Http([string]$Url, [string]$Name, [string]$Hint) {
    for ($i = 1; $i -le 5; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Log "$Name отвечает (HTTP 200)"
                return $true
            }
        }
        catch {
            # 4xx/5xx тоже долетают сюда: сервис жив, но отвечает ошибкой.
            if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -ne 0) {
                Write-Log "Попытка ${i}: $Name ответил HTTP $([int]$_.Exception.Response.StatusCode)"
            }
            else {
                Write-Log "Попытка $i : $Name ещё не отвечает, ждём 3 секунды..."
            }
        }
        Start-Sleep -Seconds 3
    }
    Write-Log "$Name не отвечает, проверьте логи: docker compose logs $Hint"
    return $false
}

# Бэкенд проверяется через прямой порт контейнера, фронтенд - через nginx-контейнер
$healthy = $true
if (-not (Test-Http "http://127.0.0.1:$ApiPort/docs" 'бэкенд' 'backend')) { $healthy = $false }
if (-not (Test-Http "http://127.0.0.1:$AppPort/" 'фронтенд' 'frontend')) { $healthy = $false }

Push-Location $ProjectDir
docker compose ps
Pop-Location

Write-Log '=========================================='
if ($healthy) {
    Write-Log 'Обновление успешно завершено!'
}
else {
    Write-Log 'Код обновлён и контейнеры пересобраны, но часть сервисов не отвечает.'
    Write-Log 'Это НЕ откат: docker compose logs backend / frontend, затем повторите up -d.'
}
Write-Log "Лог обновления: $logFile"
Write-Log '=========================================='
