# CSGOEmpire WebSocket Monitor - Complete Setup
# Run this PowerShell script to launch Chrome and start monitoring

param(
    [int]$Port = 9222,
    [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe",
    [string]$UserData = "C:\Users\haian\AppData\Local\Google\Chrome\User Data",
    [string]$Profile = "Default",
    [string]$URL = "https://csgoempire.com/withdraw/steam/market"
)

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# 1️⃣ Kill existing Chrome
Write-Info "Closing existing Chrome processes..."
try { taskkill /F /IM chrome.exe 2>$null | Out-Null } catch {}

Write-Info "Waiting for Chrome to fully close..."
Start-Sleep -Seconds 3

# Double-check Chrome is closed
$chromeProcesses = Get-Process chrome -ErrorAction SilentlyContinue
if ($chromeProcesses) {
    Write-Warn "Some Chrome processes still running, forcing close again..."
    Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 2️⃣ Launch Chrome with debugging
Write-Info "Launching Chrome on port $Port using your real profile..."
Write-Info "Profile path: $UserData\$Profile"

$chromeArgs = @(
    "--remote-debugging-port=$Port",
    "--remote-allow-origins=*",
    "--user-data-dir=$UserData",
    "--profile-directory=$Profile",
    "--no-first-run",
    "--no-default-browser-check",
    $URL
)
Start-Process -FilePath $ChromePath -ArgumentList $chromeArgs

# 3️⃣ Wait for DevTools
$devtools = "http://127.0.0.1:$Port/json"
$timeout = (Get-Date).AddSeconds(30)
$ready = $false
Write-Info "Waiting for Chrome DevTools to start..."
while ((Get-Date) -lt $timeout) {
    try {
        $null = Invoke-RestMethod -Uri $devtools -TimeoutSec 2
        $ready = $true
        break
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ready) {
    Write-Err "DevTools not responding at $devtools"
    exit 1
}
Write-Info "DevTools ready at $devtools"

# 4️⃣ Run Python monitor
if (-not (Test-Path "complete_csgoempire_monitor.py")) {
    Write-Err "Python script not found: complete_csgoempire_monitor.py"
    exit 1
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    $py = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $py = "py"
} else {
    Write-Err "Python not found in PATH."
    exit 1
}

Write-Info "Starting CSGOEmpire WebSocket monitor..."
Write-Info "The monitor will capture item names, auction data, and bidder information."
Write-Info "Press Ctrl+C to stop monitoring."
Write-Host ""

& $py complete_csgoempire_monitor.py --port $Port --match-url "csgoempire"
