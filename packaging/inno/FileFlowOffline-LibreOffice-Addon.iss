#define MyAppName "FileFlow Offline LibreOffice Addon"
#define MyAppVersion "0.2.0"
#define SourceDir "..\..\vendor"

[Setup]
AppId={{AC528411-D164-4E54-A973-FILEFLOWLO}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\FileFlow Offline
OutputBaseFilename=FileFlowOffline-LibreOffice-Addon
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
CreateAppDir=yes

[Files]
Source: "{#SourceDir}\LibreOffice\*"; DestDir: "{app}\plugins\libreoffice"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Run]
Filename: "{app}\offline-converter-agent.exe"; Parameters: "check-dependencies --json"; Flags: runhidden skipifdoesntexist
