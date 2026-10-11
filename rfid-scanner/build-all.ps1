# build-all.ps1
# Complete build: single-file, folder publish, Inno Setup, WiX MSI
# Requires: .NET 8 SDK, Inno Setup, WiX Toolset v4

param(
    [string]$Config = "Release",
    [string]$Runtime = "win-x64"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$project = Join-Path $root "RfidScanner"
$publishDir = Join-Path $project "publish"
$singleDir = Join-Path $root "singlefile"
$innoOutput = Join-Path $root "installer_output"
$wixOutput = Join-Path $root "msi_output"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  PAPI RFID Scanner - Full Build Pipeline" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ===================== STEP 1: Clean =====================
Write-Host "[1/7] Cleaning..." -ForegroundColor Yellow
@($publishDir, $singleDir, $innoOutput, $wixOutput) | Where-Object { Test-Path $_ } | ForEach-Object {
    Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue
}
@($publishDir, $singleDir, $innoOutput, $wixOutput) | ForEach-Object {
    New-Item -ItemType Directory -Force -Path $_ | Out-Null
}

# ===================== STEP 2: Restore =====================
Write-Host "[2/7] Restoring dependencies..." -ForegroundColor Yellow
dotnet restore (Join-Path $root "RfidScanner.sln") --verbosity quiet

# ===================== STEP 3: Folder Publish =====================
Write-Host "[3/7] Publishing folder (multi-file)..." -ForegroundColor Yellow
dotnet publish "$project\RfidScanner.csproj" `
    -c $Config -r $Runtime `
    --self-contained false `
    -p:PublishSingleFile=false `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -o $publishDir --verbosity quiet

$exe = Get-Item (Join-Path $publishDir "RfidScanner.exe")
$folderSize = (Get-ChildItem $publishDir -Recurse | Measure-Object Length -Sum).Sum
Write-Host "  Folder publish: $([math]::Round($folderSize/1MB,2)) MB" -ForegroundColor Green

# ===================== STEP 4: Single-file Publish =====================
Write-Host "[4/7] Publishing single-file exe..." -ForegroundColor Yellow
dotnet publish "$project\RfidScanner.csproj" `
    -c $Config -r $Runtime `
    --self-contained false `
    -p:PublishSingleFile=true `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -o $singleDir --verbosity quiet

$singleExe = Get-Item (Join-Path $singleDir "RfidScanner.exe")
Write-Host "  Single-file: $([math]::Round($singleExe.Length/1MB,2)) MB" -ForegroundColor Green

# ===================== STEP 5: Inno Setup =====================
Write-Host "[5/7] Creating Inno Setup installer..." -ForegroundColor Yellow

$isccPaths = @(
    "C:\Program Files\Inno Setup 7\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$iscc = $isccPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($iscc) {
    $iss = @'
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
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}

[Files]
Source: "PUBLISH_DIR\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\PAPI RFID Scanner"; Filename: "{app}\RfidScanner.exe"
Name: "{autodesktop}\PAPI RFID Scanner"; Filename: "{app}\RfidScanner.exe"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\RfidScanner.exe"; Description: "Launch PAPI RFID Scanner"; Flags: nowait postinstall skipifsilent
'@
    $iss = $iss -replace 'PUBLISH_DIR', $publishDir.Replace('\', '\\')
    Set-Location $root
    Set-Content -Path "installer.iss" -Value $iss -Encoding UTF8
    & $iscc "installer.iss" "/Q"
    Set-Location $root
    
    $setup = Get-Item (Join-Path $innoOutput "PAPI.RfidScanner.Setup.exe") -ErrorAction SilentlyContinue
    if (-not $setup) {
        # Inno Setup outputs to 'output/' subfolder
        $setupAlt = Get-Item (Join-Path $innoOutput "output\PAPI.RfidScanner.Setup.exe") -ErrorAction SilentlyContinue
        if ($setupAlt) {
            Copy-Item $setupAlt.FullName (Join-Path $innoOutput "PAPI.RfidScanner.Setup.exe") -Force
            $setup = $setupAlt
        }
    }
    if (-not $setup) {
        # Check root output folder
        $setupRoot = Get-Item (Join-Path $root "output\PAPI.RfidScanner.Setup.exe") -ErrorAction SilentlyContinue
        if ($setupRoot) {
            Copy-Item $setupRoot.FullName (Join-Path $innoOutput "PAPI.RfidScanner.Setup.exe") -Force
            $setup = $setupRoot
        }
    }
    if ($setup) {
        Write-Host "  Inno Setup: $([math]::Round($setup.Length/1MB,2)) MB" -ForegroundColor Green
    } else {
        Write-Host "  Inno Setup: check $innoOutput" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Inno Setup not found - skipping" -ForegroundColor Yellow
    Write-Host "  Install: https://jrsoftware.org/isdl.php" -ForegroundColor Gray
}

# ===================== STEP 6: WiX MSI =====================
Write-Host "[6/7] Creating WiX MSI installer..." -ForegroundColor Yellow

$wixPaths = @(
    (Join-Path $env:ProgramFiles "WiX Toolset v4\bin\wix.exe"),
    (Join-Path $env:ProgramFiles "WiX Toolset v3.14\bin\candle.exe"),
    (Join-Path "${env:ProgramFiles(x86)}" "WiX Toolset v3.14\bin\candle.exe")
)
$wixPath = ($wixPaths | Where-Object { Test-Path $_ } | Select-Object -First 1)
if ($wixPath -and (Test-Path $wixPath)) {
    # Use candle.exe + light.exe (WiX v3.14)
    $candleDir = Split-Path $wixPath
    $lightPath = Join-Path $candleDir "light.exe"
    $heatPath = Join-Path $candleDir "heat.exe"
    
    if (Test-Path $lightPath) {
        # Compile wxs to wxobj
        & $candleDir\candle.exe "$root\installer\Product.wxs" `
            "-out" (Join-Path $wixOutput "Product.wixobj") `
            "-dPublishDir=$publishDir" `
            "-dSourceDir=$publishDir"
        
        # Link to MSI
        & $lightPath (Join-Path $wixOutput "Product.wixobj") `
            "-out" (Join-Path $wixOutput "PAPI.RfidScanner.msi")
    }
    
    $msi = Get-Item (Join-Path $wixOutput "PAPI.RfidScanner.msi") -ErrorAction SilentlyContinue
    if ($msi) {
        Write-Host "  WiX MSI: $([math]::Round($msi.Length/1MB,2)) MB" -ForegroundColor Green
    } else {
        Write-Host "  WiX build check $wixOutput" -ForegroundColor Yellow
    }
} else {
    Write-Host "  WiX not found - skipping" -ForegroundColor Yellow
    Write-Host "  Install: winget install WiXToolset.WixToolset" -ForegroundColor Gray
}

# ===================== STEP 7: Summary =====================
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  BUILD COMPLETE" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Single-file exe:  $singleDir" -ForegroundColor Gray
Write-Host "  Folder publish:   $publishDir" -ForegroundColor Gray
Write-Host "  Inno Setup:       $innoOutput" -ForegroundColor Gray
Write-Host "  WiX MSI:          $wixOutput" -ForegroundColor Gray
Write-Host ""
