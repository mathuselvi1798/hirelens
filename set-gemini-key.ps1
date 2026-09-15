# Installs a Google Gemini API key into backend\.env and switches the app to
# the Gemini provider. The key is read with a hidden prompt, so it never
# appears on screen and cannot end up in a screenshot.

$ErrorActionPreference = "Stop"
$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $root "backend\.env"
$example = Join-Path $root "backend\.env.example"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  NEXA - install your Google Gemini key (free)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. aistudio.google.com  ->  Get API key"
Write-Host "  2. Create a key, click the copy button"
Write-Host "  3. Come back here, RIGHT-CLICK once to paste"
Write-Host "  4. Press Enter"
Write-Host ""
Write-Host "  Your key stays hidden as you paste - that is normal." -ForegroundColor DarkGray
Write-Host ""

$secure = Read-Host "  Paste your Gemini API key (hidden)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try   { $key = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
if ($key) { $key = $key.Trim().Trim('"').Trim("'") }

if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host "`n  [X] Nothing was pasted. Run this again." -ForegroundColor Red
    exit 1
}
if ($key.Length -lt 20) {
    Write-Host "`n  [X] That looks too short to be a Gemini key." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $envFile)) {
    if (Test-Path $example) { Copy-Item $example $envFile }
    else {
        Write-Host "`n  [X] Cannot find backend\.env" -ForegroundColor Red
        exit 1
    }
}

# Set GEMINI_API_KEY and flip AI_PROVIDER to gemini in one pass.
$sawKey = $false; $sawProvider = $false
$out = Get-Content $envFile | ForEach-Object {
    if ($_ -like "GEMINI_API_KEY=*") { $sawKey = $true; "GEMINI_API_KEY=$key" }
    elseif ($_ -like "AI_PROVIDER=*") { $sawProvider = $true; "AI_PROVIDER=gemini" }
    else { $_ }
}
if (-not $sawKey)      { $out += "GEMINI_API_KEY=$key" }
if (-not $sawProvider) { $out += "AI_PROVIDER=gemini" }

Set-Content -Path $envFile -Value $out -Encoding ASCII

$okKey      = Select-String -Path $envFile -Pattern '^GEMINI_API_KEY=.+' -Quiet
$okProvider = Select-String -Path $envFile -Pattern '^AI_PROVIDER=gemini' -Quiet
if (-not ($okKey -and $okProvider)) {
    Write-Host "`n  [X] The settings did not save correctly." -ForegroundColor Red
    exit 1
}

$len = $key.Length
$key = $null

Write-Host ""
Write-Host "  OK - Gemini key installed (length $len)" -ForegroundColor Green
Write-Host "  OK - provider switched to gemini" -ForegroundColor Green
Write-Host "  Nothing above reveals the key - safe to screenshot." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Next: restart the server"
Write-Host "    1. click the black API server window"
Write-Host "    2. press Ctrl+C"
Write-Host "    3. double-click  run-backend.bat"
Write-Host "    4. look for   ai_enabled=True"
