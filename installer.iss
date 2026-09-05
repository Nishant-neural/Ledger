#define MyAppName "Simple Ledger"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Simple Ledger"
#define MyAppExeName "SimpleLedger.exe"

[Setup]

AppId={{B7E3A1F2-8D4C-4A7A-9C10-5F1234567890}

AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Simple Ledger
DefaultGroupName={#MyAppName}

OutputDir=installer
OutputBaseFilename=SimpleLedgerSetup

Compression=lzma
SolidCompression=yes

WizardStyle=modern

UninstallDisplayName={#MyAppName}

[Languages]

Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]

Source: "dist\SimpleLedger\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]

Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Icons]

Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]

Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent