# run_ws_capture.ps1
# Launch Chrome with your real profile and run capture_ws_cdp.py automatically.

param(
    [int]$Port = 9222,
    [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe",
    [string]$UserData = "C:\Users\haian\AppData\Local\Google\Chrome\User Data",
    [string]$Profile = "Default",
    [string]$PythonScript = "capture_ws_cdp.py",
    [string]$URL = "https://csgoempire.com/withdraw/steam/market"
)

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# 1️⃣ Kill existing Chrome (to ensure the new one runs with remote debugging)
Write-Info "Closing existing Chrome processes..."
try { taskkill /F /IM chrome.exe 2>$null | Out-Null } catch {}

# Wait for Chrome to fully close and release the profile lock
Write-Info "Waiting for Chrome to fully close..."
Start-Sleep -Seconds 3

# Double-check that Chrome is really closed
$chromeProcesses = Get-Process chrome -ErrorAction SilentlyContinue
if ($chromeProcesses) {
    Write-Warn "Some Chrome processes still running, forcing close again..."
    Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 2️⃣ Verify paths exist
if (-not (Test-Path $ChromePath)) {
    Write-Err "Chrome not found at: $ChromePath"
    Write-Info "Please specify correct path with -ChromePath parameter"
    exit 1
}

if (-not (Test-Path $UserData)) {
    Write-Warn "User Data directory not found at: $UserData"
    Write-Warn "Chrome will create a new profile. To use your existing profile, specify correct path with -UserData parameter"
}

# 2️⃣ Launch Chrome with your real profile
Write-Info "Launching Chrome on port $Port using your real profile..."
Write-Info "Profile path: $UserData\$Profile"

# Use the correct Chrome profile path format
$chromeArgs = @(
    "--remote-debugging-port=$Port",
    "--remote-allow-origins=*",
    "--user-data-dir=`"$UserData`"",
    "--profile-directory=`"$Profile`"",
    "--no-first-run",
    "--no-default-browser-check",
    $URL
)
Start-Process -FilePath $ChromePath -ArgumentList $chromeArgs

# 3️⃣ Wait for the DevTools endpoint to become available
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
    Write-Err "DevTools not responding at $devtools. Is Chrome open with --remote-debugging-port?"
    exit 1
}
Write-Info "DevTools ready at $devtools"

# 4️⃣ Run your Python script
if (-not (Test-Path $PythonScript)) {
    Write-Err "Python script not found: $PythonScript"
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

Write-Info "Running Python capture script..."
Write-Info "The script will capture all WebSocket traffic from Chrome."
Write-Info "Press Ctrl+C to stop capturing."
Write-Host ""
& $py $PythonScript --match-url "csgoempire" --show-sent

