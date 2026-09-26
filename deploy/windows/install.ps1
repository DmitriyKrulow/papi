<#
.SYNOPSIS
    Установка PAPI на сервер Windows (Server 2019/2022 или Windows 10/11) с нуля.

.DESCRIPTION
    Скрипт выполняет:
      1. проверяет/устанавливает Docker Desktop;
      2. клонирует репозиторий в C:\papi (или обновляет существующий);
      3. создаёт .env из .env.example, генерирует пароли и секрет;
      4. освобождает порт 80 (забирает его у IIS/хостового nginx, если они есть);
      5. регистрирует задачи планировщика:
           PAPI-Start    - запуск стека при загрузке системы (автостарт контейнеров);
           PAPI-Update   - автообновление из git каждые 15 минут;
      6. открывает в брандмауэре только 80 и 8080;
      7. собирает образы и поднимает контейнеры.

    Запускать в PowerShell ОТ АДМИНИСТРАТОРА:
        Set-ExecutionPolicy Bypass -Scope Process -Force
        powershell -File .\deploy\windows\install.ps1

.PARAMETER RepoUrl
    Git-репозиторий. По умолчанию https://github.com/ditri466/TEST.git

.PARAMETER Branch
    Ветка. По умолчанию main

.PARAMETER ProjectDir
    Каталог установки. По умолчанию C:\papi

.PARAMETER SkipFirewall
    Не настраивать брандмауэр.
#>
[CmdletBinding()]
param(
    [string]$RepoUrl    = 'https://github.com/ditri466/TEST.git',
    [string]$Branch     = 'main',
    [string]$ProjectDir = 'C:\papi',
    [switch]$SkipFirewall
)

$ErrorActionPreference = 'Stop'
$AppPortDefault = 80
$ApiPortDefault = 8080

function Write-Log([string]$Message) {
    Write-Host ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $Message)
}

# --- Требование прав администратора -----------------------------------------
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Запустите PowerShell от администратора: эта установка ставит службы и правила брандмауэра.'
}

# --- 1. Docker ---------------------------------------------------------------
Write-Log '1/7. Проверка Docker'
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Log 'Docker не найден. Открываю страницу установки Docker Desktop.'
    Write-Log 'После установки перезапустите этот скрипт.'
    Start-Process 'https://www.docker.com/products/docker-desktop/'
    throw 'Docker Desktop не установлен.'
}
Write-Log ("Docker: " + (docker --version))

# Docker Desktop поднимает демон как службу; без автозапуска службы контейнеры
# после перезагрузки сервера не стартуют.
$dockerService = Get-Service -Name 'com.docker.service' -ErrorAction SilentlyContinue
if ($dockerService) {
    Set-Service -Name $dockerService.Name -StartupType Automatic
    Write-Log 'Служба com.docker.service - автозапуск включён'
}

# Гарантируем, что сам Docker Desktop стартует при входе/загрузке: без GUI-сессии
# демон не поднимется, поэтому задача планировщика (шаг 5) запускает его в лоб.
$desktopExe = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
if (-not (Test-Path $desktopExe)) {
    Write-Log "ВНИМАНИЕ: не найден '$desktopExe'. Если Docker Desktop установлен в другое место,"
    Write-Log 'поправьте путь в deploy\windows\start-papi.ps1 (параметр -DockerDesktopExe).'
}

# --- 2. Код проекта ----------------------------------------------------------
Write-Log "2/7. Код проекта в $ProjectDir"
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Log 'git не найден. Установите Git for Windows: https://git-scm.com/download/win'
    throw 'git не установлен.'
}

if (Test-Path (Join-Path $ProjectDir '.git')) {
    Write-Log 'Репозиторий уже клонирован - обновляю'
    git config --global --add safe.directory ($ProjectDir -replace '\\', '/')
    git -C $ProjectDir fetch origin $Branch
    git -C $ProjectDir reset --hard "origin/$Branch"
}
elseif ((Test-Path $ProjectDir) -and (Get-ChildItem $ProjectDir -Force | Measure-Object).Count -gt 0) {
    throw "Каталог $ProjectDir непустой и не git-репозиторий. Укажите другой -ProjectDir."
}
else {
    Write-Log "Клонирую $RepoUrl ($Branch) в $ProjectDir"
    git clone --branch $Branch $RepoUrl $ProjectDir
}

# --- 3. .env -----------------------------------------------------------------
Write-Log '3/7. Файл настроек .env'
$envFile = Join-Path $ProjectDir '.env'
if (Test-Path $envFile) {
    Write-Log '.env уже есть - существующие пароли и секреты не трогаю'
}
else {
    Copy-Item (Join-Path $ProjectDir '.env.example') $envFile

    # Значения из шаблона пригодны только для разработки.
    $dbPass = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | ForEach-Object { [char]$_ })
    $jwtKey = -join ((48..57) + (97..102) | Get-Random -Count 96 | ForEach-Object { [char]$_ })

    $lines = Get-Content $envFile -Encoding UTF8
    $lines = $lines | ForEach-Object {
        switch -Regex ($_) {
            '^POSTGRES_PASSWORD='  { "POSTGRES_PASSWORD=$dbPass"; break }
            '^SECRET_KEY='         { "SECRET_KEY=$jwtKey"; break }
            '^DATABASE_URL='       { "DATABASE_URL=postgresql+psycopg2://postgres:${dbPass}@localhost:5432/papidb"; break }
            default                { $_ }
        }
    }
    Set-Content -Path $envFile -Value $lines -Encoding UTF8

    Write-Log '.env создан, сгенерированы POSTGRES_PASSWORD и SECRET_KEY'
    Write-Log 'Проверьте CORS_ORIGINS и FRONTEND_URL - в шаблоне указан http://localhost'
}

function Get-EnvValue([string]$Name, [string]$Default) {
    $line = Select-String -Path $envFile -Pattern "^\s*$Name=" | Select-Object -Last 1
    if ($line) {
        $value = ($line.Line -split '=', 2)[1].Trim().Trim('"')
        if ($value) { return $value }
    }
    return $Default
}

$AppPort = Get-EnvValue 'APP_PORT' $AppPortDefault
$ApiPort = Get-EnvValue 'API_PORT' $ApiPortDefault

# --- 4. Порт 80 --------------------------------------------------------------
Write-Log "4/7. Проверка, что порт $AppPort свободен"
$owner = Get-NetTCPConnection -LocalPort $AppPort -State Listen -ErrorAction SilentlyContinue |
         Select-Object -First 1
if ($owner) {
    $ownerProcess = (Get-Process -Id $owner.OwningProcess -ErrorAction SilentlyContinue).ProcessName
    Write-Log "Порт $AppPort занят процессом '$ownerProcess' (PID $($owner.OwningProcess))"

    # Классика Windows-сервера - IIS (W3SVC) занимает 80 через http.sys.
    foreach ($svcName in @('W3SVC', 'w3svc')) {
        $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -ne 'Stopped') {
            Write-Log "Останавливаю и отключаю службу $svcName (IIS) - порт нужен контейнеру"
            Stop-Service -Name $svcName -Force
            Set-Service -Name $svcName -StartupType Disabled
        }
    }
    $owner = Get-NetTCPConnection -LocalPort $AppPort -State Listen -ErrorAction SilentlyContinue |
             Select-Object -First 1
    if ($owner) {
        Write-Log "Порт $AppPort по-прежнему занят. Освободите его и повторите установку,"
        Write-Log "либо смените APP_PORT в $envFile."
        throw "Порт $AppPort недоступен."
    }
    Write-Log 'Порт освобождён'
}
else {
    Write-Log "Порт $AppPort свободен"
}

# --- 5. Задачи планировщика --------------------------------------------------
Write-Log '5/7. Задачи планировщика: автостарт и автообновление'
$startScript = Join-Path $ProjectDir 'deploy\windows\start-papi.ps1'
$updateScript = Join-Path $ProjectDir 'deploy\windows\update.ps1'

# Автостарт контейнеров после перезагрузки сервера.
# Триггер - именно загрузка системы (NotTrigonLogonType), чтобы сервер поднимал
# приложение без входа пользователя в сессию.
$actionStart = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startScript`""
$triggerStart = New-ScheduledTaskTrigger -AtStartup
$settingsStart = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2)
$principalStart = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName 'PAPI-Start' `
    -Action $actionStart -Trigger $triggerStart -Settings $settingsStart `
    -Principal $principalStart `
    -Description 'PAPI: запуск docker-стека при загрузке сервера' -Force | Out-Null
Write-Log 'Задача PAPI-Start зарегистрирована (старт при загрузке)'

# Автообновление из git каждые 15 минут.
$actionUpdate = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$updateScript`""
$triggerUpdate = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 15)
$settingsUpdate = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)
$principalUpdate = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName 'PAPI-Update' `
    -Action $actionUpdate -Trigger $triggerUpdate -Settings $settingsUpdate `
    -Principal $principalUpdate `
    -Description 'PAPI: автообновление из git каждые 15 минут' -Force | Out-Null
Write-Log 'Задача PAPI-Update зарегистрирована (каждые 15 минут)'

# --- 6. Брандмауэр -----------------------------------------------------------
Write-Log "6/7. Брандмауэр: вход разрешён только на $AppPort и $ApiPort"
if ($SkipFirewall) {
    Write-Log 'Пропущено (-SkipFirewall)'
}
else {
    # Правила docker уже открывают публикуемые порты; эти правила делают
    # поведение явным и переживают переустановку docker.
    foreach ($rule in @(@{ Port = $AppPort; What = 'PAPI web' }, @{ Port = $ApiPort; What = 'PAPI api' })) {
        $name = "PAPI-In-$($rule.Port)"
        if (-not (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -DisplayName $name `
                -Direction Inbound -Action Allow -Protocol TCP `
                -LocalPort $rule.Port -Profile Any | Out-Null
            Write-Log "Разрешён вход: TCP $($rule.Port) ($($rule.What))"
        }
        else {
            Write-Log "Правило $name уже есть"
        }
    }
    Write-Log 'Других входящих правил для приложения не создавали:'
    Write-Log 'список открытых портов определяется секциями ports в docker-compose.yml.'
}

# --- 7. Сборка и запуск ------------------------------------------------------
Write-Log '7/7. Сборка образов и запуск контейнеров'
Push-Location $ProjectDir
try {
    docker compose up -d --build
    Start-Sleep -Seconds 5
    docker compose ps
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Веб-интерфейсы:'
Write-Host "  приложение : http://$env:COMPUTERNAME`:$AppPort"
Write-Host "  API (docs) : http://$env:COMPUTERNAME`:$ApiPort/docs"
Write-Host ''
Write-Host 'Дальше:'
Write-Host "  вручную обновить  : powershell -File $ProjectDir\deploy\windows\update.ps1"
Write-Host '  посмотреть задачи : Get-ScheduledTask -TaskName PAPI-*'
Write-Host '  логи контейнеров  : docker compose logs -f backend'
