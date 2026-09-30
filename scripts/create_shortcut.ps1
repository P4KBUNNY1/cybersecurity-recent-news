# Creates two desktop shortcuts that launch scripts\start_cyber_intel.bat
$scripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$root    = Split-Path -Parent $scripts
$desktop = [Environment]::GetFolderPath('Desktop')
$ws      = New-Object -ComObject WScript.Shell

$items = @(
  @{ Name = 'Cyber Intel Board';             Args = ''     },
  @{ Name = 'Cyber Intel Board (view only)'; Args = 'view' }
)
foreach ($i in $items) {
  $lnk = $ws.CreateShortcut("$desktop\$($i.Name).lnk")
  $lnk.TargetPath       = "$scripts\start_cyber_intel.bat"
  $lnk.Arguments        = $i.Args
  $lnk.WorkingDirectory = $root
  $lnk.IconLocation     = "$env:SystemRoot\System32\shell32.dll,13"
  $lnk.Save()
  Write-Host "Created: $desktop\$($i.Name).lnk"
}
