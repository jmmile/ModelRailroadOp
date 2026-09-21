param([string]$Compiler = '')
$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectDirectory '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'Create the project .venv and install requirements-build.txt and requirements.txt first.'
}
$buildArguments = @((Join-Path $PSScriptRoot 'release_build.py'))
if ($Compiler) { $buildArguments += @('--compiler', $Compiler) }
& $python @buildArguments
if ($LASTEXITCODE -ne 0) { throw 'Release failed. See build\release-logs for details. No new release was published.' }
