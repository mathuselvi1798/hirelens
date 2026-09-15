# Connects this local repository to a GitHub repository and pushes.
#
# This script never sees your GitHub password or any token. When git needs to
# authenticate, Git Credential Manager opens a browser window and you sign in
# to GitHub directly. That is the correct way for a credential to be handled:
# between you and GitHub, with nothing in between.

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Say($text, $color = "White") { Write-Host "  $text" -ForegroundColor $color }

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  NEXA - push to GitHub" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".git")) {
    Say "[X] No repository here. Run commit-nexa.bat first." Red
    exit 1
}

git rev-parse --verify HEAD *>$null
if ($LASTEXITCODE -ne 0) {
    Say "[X] Nothing committed yet. Run commit-nexa.bat first." Red
    exit 1
}

Write-Host "  Before running this, on github.com:" -ForegroundColor Yellow
Write-Host ""
Write-Host "    1. Click + (top right)  ->  New repository"
Write-Host "    2. Name it:  nexa-ai-analyzer"
Write-Host "    3. Choose Public or Private"
Write-Host "    4. Do NOT tick 'Add a README', '.gitignore' or 'license'"
Write-Host "       - this project already has all three, and ticking them"
Write-Host "         creates a conflict you would have to untangle"
Write-Host "    5. Click 'Create repository'"
Write-Host "    6. Copy the URL shown, e.g."
Write-Host "       https://github.com/yourname/nexa-ai-analyzer.git" -ForegroundColor Gray
Write-Host ""

$url = Read-Host "  Paste the repository URL"
$url = $url.Trim().Trim('"')

if ($url -notmatch '^https://github\.com/[^/]+/[^/]+?(\.git)?$') {
    Say "[X] That does not look like a GitHub HTTPS URL." Red
    Say "    Expected: https://github.com/yourname/nexa-ai-analyzer.git" DarkGray
    exit 1
}
if ($url -notmatch '\.git$') { $url = "$url.git" }

# --- one last safety check before anything leaves this machine ------------
$tracked = @(git ls-files)
$leaked = $tracked | Where-Object {
    $_ -match '(^|/)\.env$' -or $_ -match '\.pem$' -or $_ -match '\.key$'
}
if ($leaked) {
    Write-Host ""
    Say "[X] STOPPING - these are committed and would become visible:" Red
    $leaked | ForEach-Object { Say "      $_" Red }
    Say "    Nothing was pushed. Tell Claude." DarkGray
    exit 1
}
Say "Safety check passed - no secrets in the commit history." Green

# --- remote ---------------------------------------------------------------
git remote get-url origin *>$null
if ($LASTEXITCODE -eq 0) {
    git remote set-url origin $url
    Say "Updated remote 'origin'."
} else {
    git remote add origin $url
    Say "Added remote 'origin'."
}

git branch -M main *>$null

# --- push -----------------------------------------------------------------
Write-Host ""
Say "Pushing... a browser window may open for you to sign in to GitHub." Yellow
Write-Host ""
git push -u origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Say "[X] Push failed. Common causes:" Red
    Say "    - sign-in was cancelled or timed out" DarkGray
    Say "    - the repository already has commits (you ticked 'Add a README')" DarkGray
    Say "    - the URL points at a repository you cannot write to" DarkGray
    Say "    Send Claude the red text above." DarkGray
    exit 1
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Pushed. Your project is on GitHub." -ForegroundColor Green
Write-Host "  $($url -replace '\.git$','')" -ForegroundColor White
Write-Host ""
Write-Host "  From now on: run commit-nexa.bat to commit," -ForegroundColor White
Write-Host "  then 'git push' to upload the changes." -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
