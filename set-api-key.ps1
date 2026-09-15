# Installs an Anthropic API key into backend\.env
#
# The key is read with a hidden prompt, so it never appears on screen, never
# lands in shell history, and cannot end up in a screenshot. Only its length
# is reported back, as confirmation that the write succeeded.

$ErrorActionPreference = "Stop"
$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $root "backend\.env"
$example = Join-Path $root "backend\.env.example"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  NEXA - install your Anthropic API key" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. console.anthropic.com  ->  API keys"
Write-Host "  2. Create a key, click 'Copy key'"
Write-Host "  3. Come back here, RIGHT-CLICK once to paste"
Write-Host "  4. Press Enter"
Write-Host ""
Write-Host "  Your key stays hidden as you paste - that is normal." -ForegroundColor DarkGray
Write-Host "  It is written only to backend\.env on this computer." -ForegroundColor DarkGray
Write-Host ""

$secure = Read-Host "  Paste your API key (hidden)" -AsSecureString

$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try   { $key = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }

if ($key) { $key = $key.Trim().Trim('"').Trim("'") }

if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host ""
    Write-Host "  [X] Nothing was pasted. Run this again." -ForegroundColor Red
    Write-Host "      Paste with a single RIGHT-CLICK in this window." -ForegroundColor DarkGray
    exit 1
}

if (-not $key.StartsWith("sk-ant-")) {
    Write-Host ""
    Write-Host "  [X] That does not look like an Anthropic API key." -ForegroundColor Red
    Write-Host "      It should begin with  sk-ant-" -ForegroundColor DarkGray
    exit 1
}

if (-not (Test-Path $envFile)) {
    if (Test-Path $example) { Copy-Item $example $envFile }
    else {
        Write-Host ""
        Write-Host "  [X] Cannot find backend\.env" -ForegroundColor Red
        Write-Host "      Keep this file inside the nexa-ai-analyzer folder." -ForegroundColor DarkGray
        exit 1
    }
}

$replaced = $false
$out = Get-Content $envFile | ForEach-Object {
    if ($_ -like "ANTHROPIC_API_KEY=*") { $replaced = $true; "ANTHROPIC_API_KEY=$key" }
    else { $_ }
}
if (-not $replaced) { $out += "ANTHROPIC_API_KEY=$key" }

Set-Content -Path $envFile -Value $out -Encoding ASCII

# Read back and confirm, rather than trusting the write.
if (-not (Select-String -Path $envFile -Pattern '^ANTHROPIC_API_KEY=sk-ant-' -Quiet)) {
    Write-Host ""
    Write-Host "  [X] The key did not save correctly." -ForegroundColor Red
    exit 1
}

$len = $key.Length
$key = $null

Write-Host ""
Write-Host "  OK - key installed in backend\.env (length $len)" -ForegroundColor Green
Write-Host "  Nothing above reveals the key - safe to screenshot." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Next: restart the server"
Write-Host "    1. click the black API server window"
Write-Host "    2. press Ctrl+C"
Write-Host "    3. double-click  run-backend.bat"
Write-Host "    4. look for   ai_enabled=True"
