[Setup]
AppId={{063AA8F8-5F95-49CF-95A9-E0BA0F6A9332}
AppName=Model Railroad Operations
AppVersion=1.0.0
DefaultDirName={localappdata}\Programs\Model Railroad Operations
DefaultGroupName=Model Railroad Operations
PrivilegesRequired=lowest
MinVersion=10.0.17763
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=ModelRailroadOperations-Setup-1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Model Railroad Operations.exe
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\Model Railroad Operations\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Model Railroad Operations"; Filename: "{app}\Model Railroad Operations.exe"
Name: "{autodesktop}\Model Railroad Operations"; Filename: "{app}\Model Railroad Operations.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Model Railroad Operations.exe"; Description: "Launch Model Railroad Operations"; Flags: nowait postinstall skipifsilent
