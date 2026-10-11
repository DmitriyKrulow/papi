# build-installer.ps1
# Build and create installer for RFID Scanner
# Requires: .NET 8 SDK, Inno Setup (https://jrsoftware.org/isdl.php)

param(
    [string]$Config = "Release",
    [string]$Runtime = "win-x64",
    [switch]$SkipInno
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Join-Path $projectRoot "RfidScanner"
$publishDir = Join-Path $projectDir "publish"
$outputDir = Join-Path $projectRoot "installer_output"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  PAPI RFID Scanner - Build & Installer" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Clean
Write-Host "[1/4] Cleaning old builds..." -ForegroundColor Yellow
if (Test-Path $publishDir) { Remove-Item $publishDir -Recurse -Force }
if (Test-Path $outputDir) { Remove-Item $outputDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $publishDir | Out-Null
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

# 2. Restore
Write-Host "[2/4] Restoring dependencies..." -ForegroundColor Yellow
dotnet restore "$projectRoot\RfidScanner.sln" --verbosity quiet

# 3. Publish
Write-Host "[3/4] Compiling Release ($Runtime)..." -ForegroundColor Yellow
dotnet publish "$projectDir\RfidScanner.csproj" `
    -c $Config `
    -r $Runtime `
    --self-contained false `
    -p:PublishSingleFile=false `
    -p:PublishReadyToRun=false `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -o $publishDir `
    --verbosity quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

$exeSize = (Get-Item (Join-Path $publishDir "RfidScanner.exe")).Length
Write-Host "  Done: RfidScanner.exe ($([math]::Round($exeSize/1MB, 2)) MB)" -ForegroundColor Green

# 4. Create installer
if (-not $SkipInno) {
    Write-Host ""
    Write-Host "[4/4] Creating Inno Setup installer..." -ForegroundColor Yellow
    
    # Find Inno Setup
    $isccPaths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $iscc = $isccPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    
    if (-not $iscc) {
        Write-Host "  Inno Setup not found!" -ForegroundColor Yellow
        Write-Host "  Install from: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
        Write-Host "  Publish folder: $publishDir" -ForegroundColor Yellow
        exit 0
    }
    
    # Create Inno Setup script
    $issContent = @'
[Setup]
AppName=PAPI RFID Scanner
AppVersion=1.0.0
AppPublisher=PAPI
AppSupportURL=https://github.com/DmitriyKrulow/papi
DefaultDirName={autopf}\PAPI\RfidScanner
DefaultGroupName=PAPI RFID Scanner
OutputDir=output
OutputBaseFilename=PAPI.RfidScanner.Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern

[Files]
Source: "publish\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\PAPI RFID Scanner"; Filename: "{app}\RfidScanner.exe"
Name: "{autodesktop}\PAPI RFID Scanner"; Filename: "{app}\RfidScanner.exe"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\RfidScanner.exe"; Description: "Launch PAPI RFID Scanner"; Flags: nowait postinstall skipifsilent
'@

    Set-Content -Path "installer.iss" -Value $issContent -Encoding UTF8
    
    # Compile
    $isccArgs = @("installer.iss", "/Q")
    & $iscc $isccArgs
    
    if ($LASTEXITCODE -eq 0) {
        $setupFile = Get-Item "$outputDir\PAPI.RfidScanner.Setup.exe"
        if ($setupFile) {
            Write-Host "  Installer created: $setupFile" -ForegroundColor Green
            Write-Host "  Size: $([math]::Round($setupFile.Length/1MB, 2)) MB" -ForegroundColor Green
        }
    } else {
        Write-Host "  Installer creation failed!" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Done!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Publish folder: $publishDir" -ForegroundColor Gray
Write-Host "Installer: $outputDir" -ForegroundColor Gray
Write-Host ""
