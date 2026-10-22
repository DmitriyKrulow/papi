# Скрипт для создания установочных файлов RfidScanner
# Запуск: .\build-installer.ps1

$ErrorActionPreference = "Stop"
$projectDir = "F:\Code\papi\rfid-scanner\RfidScanner"
$outputDir = "F:\Code\papi\rfid-scanner\installer"
$version = "1.0.0"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RfidScanner - Создание установочных файлов" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Шаг 1: Остановка запущенного процесса
Write-Host "[1/4] Остановка запущенного сканера..." -ForegroundColor Yellow
Get-Process RfidScanner -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "      Готово" -ForegroundColor Green
Write-Host ""

# Шаг 2: Publish проекта
Write-Host "[2/4] Компиляция Release версии..." -ForegroundColor Yellow
dotnet publish $projectDir -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -p:PublishReadyToRun=true -p:IncludeNativeLibrariesForSelfExtract=true -o $outputDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ОШИБКА: Не удалось скомпилировать" -ForegroundColor Red
    exit 1
}
Write-Host "      Готово" -ForegroundColor Green
Write-Host ""

# Шаг 3: Создание ZIP-архива
$zipPath = "F:\Code\papi\rfid-scanner\RfidScanner_${version}_${timestamp}.zip"
Write-Host "[3/4] Создание ZIP-архива: $zipPath" -ForegroundColor Yellow
Compress-Archive -Path "${outputDir}\*" -DestinationPath $zipPath -Force
Write-Host "      Размер: $([math]::Round((Get-Item $zipPath).Length / 1MB, 2)) MB" -ForegroundColor Green
Write-Host ""

# Шаг 4: Информация
Write-Host "[4/4] Готово!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Результаты:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  📁 Папка с файлами: $outputDir" -ForegroundColor White
Write-Host "  📦 ZIP-архив: $zipPath" -ForegroundColor White
Write-Host ""
Write-Host "  Для установки:" -ForegroundColor Yellow
Write-Host "    1. Распакуйте ZIP-архив" -ForegroundColor White
Write-Host "    2. Запустите RfidScanner.exe" -ForegroundColor White
Write-Host ""
