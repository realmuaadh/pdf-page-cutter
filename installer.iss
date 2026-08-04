#define MyAppName      "PDF Page Cutter"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "PDF Page Cutter"
#define MyAppExeName   "PDF Page Cutter.exe"
#define MyAppURL       "https://github.com"

[Setup]
AppId={{A3F2C8D1-4B7E-4F9A-8C2D-1E5F7A3B9C0D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=PDFPageCutter_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=PDF Page Cutter - Extract pages from PDF files
SetupIconFile=pdf_cutter.ico

; Show language selection dialog
ShowLanguageDialog=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; \
  InfoBeforeFile: "installer_notes_en.rtf"
Name: "arabic";  MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
  GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; \
  GroupDescription: "{cm:AdditionalIcons}"; \
  Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(MyAppName,'&','&&')}}"; \
  Flags: nowait postinstall skipifsilent

; Write chosen language to app settings on install
[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  SettingsDir, SettingsFile, LangCode: String;
  Lines: TArrayOfString;
begin
  if CurStep = ssPostInstall then
  begin
    if ActiveLanguage = 'arabic' then
      LangCode := '"ar"'
    else
      LangCode := '"en"';

    SettingsDir  := ExpandConstant('{userappdata}\PDFPageCutter');
    SettingsFile := SettingsDir + '\settings.json';

    ForceDirectories(SettingsDir);
    SetArrayLength(Lines, 1);
    Lines[0] := '{"lang": ' + LangCode + '}';
    SaveStringsToFile(SettingsFile, Lines, False);
  end;
end;
