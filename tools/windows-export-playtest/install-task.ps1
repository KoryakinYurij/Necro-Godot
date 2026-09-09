param(
    [string]$Config = "$PSScriptRoot\config.local.json"
)

$ErrorActionPreference = "Stop"
$configPath = (Resolve-Path $Config).Path
$configData = Get-Content -Raw $configPath | ConvertFrom-Json
$toolDir = $PSScriptRoot
$launcher = Join-Path $toolDir "task_launcher.py"
$templatePath = Join-Path $toolDir "task-template.xml"

if (-not (Test-Path $configData.wcu_python)) {
    throw "WCU Python not found: $($configData.wcu_python)"
}
if (-not (Test-Path $launcher)) {
    throw "Launcher not found: $launcher"
}

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$escape = [System.Security.SecurityElement]::Escape
$xml = Get-Content -Raw $templatePath
$xml = $xml.Replace("__AUTHOR__", $escape.Invoke($identity.Name))
$xml = $xml.Replace("__USER_SID__", $escape.Invoke($identity.User.Value))
$xml = $xml.Replace("__WCU_PYTHON__", $escape.Invoke([string]$configData.wcu_python))
$xml = $xml.Replace("__LAUNCHER__", $escape.Invoke($launcher))
$xml = $xml.Replace("__CONFIG__", $escape.Invoke($configPath))
$xml = $xml.Replace("__TOOL_DIR__", $escape.Invoke($toolDir))

$tempXml = Join-Path $env:TEMP "Necro-Export-Playtest.xml"
[System.IO.File]::WriteAllText(
    $tempXml,
    $xml,
    [System.Text.Encoding]::Unicode
)

try {
    & schtasks.exe /Create /TN "Necro-Export-Playtest" /XML $tempXml /F
    if ($LASTEXITCODE -ne 0) {
        throw "schtasks /Create failed with exit code $LASTEXITCODE"
    }
    Write-Host "Installed manual interactive task: Necro-Export-Playtest"
    Write-Host "Run with: schtasks /Run /TN \"Necro-Export-Playtest\""
}
finally {
    Remove-Item $tempXml -ErrorAction SilentlyContinue
}
