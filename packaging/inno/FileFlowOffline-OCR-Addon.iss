#define MyAppName "FileFlow Offline OCR Addon"
#define MyAppVersion "0.2.0"
#define VendorDir "..\..\vendor"
#define AddonDir "..\addons\ocr"

[Setup]
AppId={{B21B4FEF-88B2-4921-9A3E-FILEFLOWOCR}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\FileFlow Offline
OutputBaseFilename=FileFlowOffline-OCR-Addon
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
CreateAppDir=yes

[Files]
Source: "{#AddonDir}\python\*"; DestDir: "{app}\plugins\ocr\python"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "{#VendorDir}\paddleocr\*"; DestDir: "{app}\plugins\ocr\paddleocr"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Run]
Filename: "{app}\offline-converter-agent.exe"; Parameters: "check-dependencies --json"; Flags: runhidden skipifdoesntexist
