# launch_chrome.ps1
# Simple Chrome launcher with debugging enabled
# This is the WORKING version from Version 1

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

# 2️⃣ Verify paths exist
if (-not (Test-Path $ChromePath)) {
    Write-Err "Chrome not found at: $ChromePath"
    exit 1
}

if (-not (Test-Path $UserData)) {
    Write-Warn "User Data directory not found at: $UserData"
}

# 3️⃣ Launch Chrome with debugging
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

# 4️⃣ Wait for DevTools
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
Write-Info "Chrome is ready! You can now start tracking."
exit 0

