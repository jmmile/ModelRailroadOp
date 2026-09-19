param([string]$Compiler = 'C:\Program Files\Inno Setup 7\ISCC.exe')
$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
Push-Location $projectDirectory
try {
    & '.\.venv\Scripts\python.exe' -m PyInstaller --noconfirm ModelRailroadOperations.spec
    if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
    & $Compiler 'packaging\installer.iss'
    if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }
} finally {
    Pop-Location
}
