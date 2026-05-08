#define MyAppName "FileFlow Offline"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "FileFlow Offline"
#define SourceDir "..\..\dist-core\FileFlowOffline-Core"

[Setup]
AppId={{3C4D5F52-7C4A-4ED5-9274-FILEFLOW0200}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\FileFlow Offline
DefaultGroupName=FileFlow Offline
OutputBaseFilename=FileFlowOffline-Core-Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\离线文件转换器.exe

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FileFlow Offline"; Filename: "{app}\离线文件转换器.exe"
Name: "{group}\FileFlow Agent CLI"; Filename: "{app}\offline-converter-agent.exe"
Name: "{commondesktop}\FileFlow Offline"; Filename: "{app}\离线文件转换器.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式:"

[Run]
Filename: "{app}\offline-converter-agent.exe"; Parameters: "check-dependencies --json"; Flags: runhidden
