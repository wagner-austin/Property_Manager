param(
  [ValidateSet("start","stop","status")] [string]$action = "start",
  [int]$port = 8000
)

$root    = (Split-Path $PSScriptRoot -Parent)
$pidFile = Join-Path $root ".server.pid"

function IsRunning([int]$pid) {
  try { Get-Process -Id $pid -ErrorAction Stop | Out-Null; $true } catch { $false }
}

switch ($action) {
  "start" {
    if (Test-Path $pidFile) {
      $pid = [int](Get-Content $pidFile)
      if (IsRunning $pid) { Write-Host "Already running (PID $pid) at http://localhost:$port"; exit 0 }
      Remove-Item $pidFile -Force
    }
    $py = (Get-Command python -ErrorAction SilentlyContinue) ?? (Get-Command python3 -ErrorAction SilentlyContinue)
    if (-not $py) { Write-Error "python not found in PATH"; exit 1 }
    $p = Start-Process $py.Source -ArgumentList "-m http.server $port" -PassThru -WorkingDirectory $root -WindowStyle Hidden
    $p.Id | Out-File -Encoding ascii $pidFile
    Write-Host "Started http://localhost:$port  (PID $($p.Id))"
    Write-Host "Open: http://localhost:$port/?site=lancaster-12"
  }
  "stop" {
    if (Test-Path $pidFile) {
      $pid = [int](Get-Content $pidFile)
      if (IsRunning $pid) { Stop-Process -Id $pid -Force; Write-Host "Stopped (PID $pid)" }
      Remove-Item $pidFile -Force
    } else {
      Write-Host "No PID file; nothing to stop."
    }
  }
  "status" {
    if (Test-Path $pidFile) {
      $pid = [int](Get-Content $pidFile)
      if (IsRunning $pid) { Write-Host "Running (PID $pid) at http://localhost:$port" } else { Write-Host "Not running" }
    } else { Write-Host "Not running" }
  }
}