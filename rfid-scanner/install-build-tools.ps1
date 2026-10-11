# install-build-tools.ps1
# Скрипт установки инструментов сборки для RFID Scanner
# Требует ручной загрузки файлов если автоматическая не сработает

param(
    [string]$InstallDir = "C:\BuildTools"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  PAPI RFID Scanner - Install Build Tools" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ===================== Check what's already installed =====================
Write-Host "[1/3] Checking existing installations..." -ForegroundColor Yellow

$innoFound = $false
$isccPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
foreach ($path in $isccPaths) {
    if (Test-Path $path) {
        Write-Host "  Inno Setup: already installed at $path" -ForegroundColor Green
        $innoFound = $true
        break
    }
}
if (-not $innoFound) {
    Write-Host "  Inno Setup: NOT installed" -ForegroundColor Red
}

$wixFound = $false
$wixPaths = @(
    "C:\Program Files\WiX Toolset v4.0",
    "C:\Program Files (x86)\WiX Toolset v4.0"
)
foreach ($path in $wixPaths) {
    if (Test-Path $path) {
        Write-Host "  WiX Toolset: already installed at $path" -ForegroundColor Green
        $wixFound = $true
        break
    }
}
if (-not $wixFound) {
    Write-Host "  WiX Toolset: NOT installed" -ForegroundColor Red
}

# ===================== Download URLs =====================
Write-Host ""
Write-Host "[2/3] Download URLs:" -ForegroundColor Yellow
Write-Host "  Inno Setup: https://jrsoftware.org/download.php/iss.exe" -ForegroundColor Gray
Write-Host "  WiX Toolset: https://github.com/wixtoolset/wix3/releases/download/wix3140rtm/wix314.exe" -ForegroundColor Gray
Write-Host ""

# ===================== Instructions =====================
if (-not $innoFound -or -not $wixFound) {
    Write-Host "[3/3] MANUAL INSTALLATION REQUIRED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Due to network restrictions, automatic download failed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install manually:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. Inno Setup (for .exe installer):" -ForegroundColor White
    Write-Host "     a) Open: https://jrsoftware.org/isdl.php" -ForegroundColor Gray
    Write-Host "     b) Download 'Inno Setup 6.3.x Setup.exe'" -ForegroundColor Gray
    Write-Host "     c) Run: InnoSetup.exe /DIR=`"C:\Program Files (x86)\Inno Setup 6`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. WiX Toolset v4 (for .msi installer):" -ForegroundColor White
    Write-Host "     a) Open: https://github.com/wixtoolset/wix3/releases" -ForegroundColor Gray
    Write-Host "     b) Download 'wix314.exe' (v3.14) OR 'wixnet40.exe' (v4)" -ForegroundColor Gray
    Write-Host "     c) Run installer" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. After installation, run:" -ForegroundColor White
    Write-Host "     .\build-all.ps1" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "[3/3] All tools installed! Run build:" -ForegroundColor Green
    Write-Host "     .\build-all.ps1" -ForegroundColor Cyan
    Write-Host ""
}
