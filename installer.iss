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
Source: "F:\\Code\\papi\\rfid-scanner\\RfidScanner\\publish\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\PAPI RFID Scanner"; Filename: "{app}\RfidScanner.exe"
Name: "{autodesktop}\PAPI RFID Scanner"; Filename: "{app}\RfidScanner.exe"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\RfidScanner.exe"; Description: "Launch PAPI RFID Scanner"; Flags: nowait postinstall skipifsilent
