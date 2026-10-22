# Скрипт for creating RfidScanner installer files
# Run: .\build-installer.ps1

$ErrorActionPreference = "Stop"
$projectDir = "F:\Code\papi\rfid-scanner\RfidScanner"
$outputDir = "F:\Code\papi\rfid-scanner\installer"
$version = "1.0.0"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RfidScanner - Build Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop running process
Write-Host "[1/4] Stopping running scanner..." -ForegroundColor Yellow
Get-Process RfidScanner -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "      Done" -ForegroundColor Green
Write-Host ""

# Step 2: Publish project
Write-Host "[2/4] Compiling Release version..." -ForegroundColor Yellow
dotnet publish $projectDir -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -p:PublishReadyToRun=true -p:IncludeNativeLibrariesForSelfExtract=true -o $outputDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR: Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "      Done" -ForegroundColor Green
Write-Host ""

# Step 3: Create ZIP archive
$zipPath = "F:\Code\papi\rfid-scanner\RfidScanner_${version}_${timestamp}.zip"
Write-Host "[3/4] Creating ZIP archive: $zipPath" -ForegroundColor Yellow
Compress-Archive -Path "${outputDir}\*" -DestinationPath $zipPath -Force
Write-Host "      Size: $([math]::Round((Get-Item $zipPath).Length / 1MB, 2)) MB" -ForegroundColor Green
Write-Host ""

# Step 4: Summary
Write-Host "[4/4] Done!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Results:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Folder: $outputDir" -ForegroundColor White
Write-Host "  ZIP: $zipPath" -ForegroundColor White
Write-Host ""
Write-Host "  To install:" -ForegroundColor Yellow
Write-Host "    1. Extract ZIP archive" -ForegroundColor White
Write-Host "    2. Run RfidScanner.exe" -ForegroundColor White
Write-Host ""
