# Puts this project under version control and makes the first commit.
#
# Nothing is uploaded anywhere. This is entirely local: it creates the repo,
# checks that no secret is about to be committed, and commits. Pushing to
# GitHub is a separate, deliberate step you do afterwards.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Say($text, $color = "White") { Write-Host "  $text" -ForegroundColor $color }

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  NEXA - set up version control" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# --- git present? ---------------------------------------------------------
try { $v = git --version } catch {
    Say "[X] Git is not installed." Red
    Say "    Download it from https://git-scm.com/download/win" DarkGray
    Say "    Install with all the default options, then run this again." DarkGray
    exit 1
}
Say "$v detected." Green

# --- identity -------------------------------------------------------------
$name  = git config user.name
$email = git config user.email
if (-not $name -or -not $email) {
    Write-Host ""
    Say "Git needs a name and email to label commits." Yellow
    if (-not $name)  { $name  = Read-Host "  Your name" }
    if (-not $email) { $email = Read-Host "  Your email" }
    git config --global user.name  "$name"
    git config --global user.email "$email"
    Say "Saved as $name <$email>" Green
} else {
    Say "Commits will be authored by $name <$email>"
}

# --- init -----------------------------------------------------------------
if (Test-Path ".git") {
    Say "Repository already exists here." Yellow
} else {
    git init -b main | Out-Null
    Say "Repository created (branch: main)." Green
}

# --- safety check: nothing secret may be staged ---------------------------
git add -A
$staged = git diff --cached --name-only

$danger = $staged | Where-Object {
    $_ -match '(^|/)\.env$' -or $_ -match '\.env\.(local|production)$' -or $_ -match '\.pem$' -or $_ -match '\.key$'
}
if ($danger) {
    Write-Host ""
    Say "[X] STOPPING - these would be committed and must not be:" Red
    $danger | ForEach-Object { Say "      $_" Red }
    Say "    Check .gitignore before continuing. Nothing was committed." DarkGray
    git reset | Out-Null
    exit 1
}
Say "Safety check passed - no .env or key files staged." Green

# Double-check the key really is invisible to git.
$envTracked = git check-ignore backend/.env 2>$null
if ($envTracked) { Say "backend\.env is correctly ignored by git." Green }
else { Say "[!] backend\.env is NOT ignored - stop and tell Claude." Red; git reset | Out-Null; exit 1 }

$count = ($staged | Measure-Object).Count
Say "$count files staged."

# --- commit ---------------------------------------------------------------
$existing = git rev-parse --verify HEAD 2>$null
if ($existing) {
    git commit -m "Update NEXA AI Analyzer" | Out-Null
    Say "Committed changes." Green
} else {
    $msg = @"
Initial commit: NEXA AI Analyzer

Backend (FastAPI):
- Centralised config, structured logging, framework-free domain errors
- Document pipeline: PDF/DOCX/TXT extraction, section, bullet and contact detection
- AI layer: provider interface (Anthropic + Gemini), schema-validated structured
  output, informed retry on invalid responses, transient-outage retry, content cache
- Analysis module registry with four modules: resume analysis, job match,
  ATS analysis, career intelligence
- 44 tests, no network calls required

Frontend (Next.js 15 + TypeScript + Tailwind):
- Dashboard with upload, job description, module selection
- One result view per module, mapped through a frontend registry
- Loading, empty and error states; provider-aware error hints
"@
    git commit -m $msg | Out-Null
    Say "First commit created." Green
}

Write-Host ""
git --no-pager log --oneline -5
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Done. Your work now has history and undo." -ForegroundColor Cyan
Write-Host ""
Write-Host "  To put it on GitHub, tell Claude and follow" -ForegroundColor White
Write-Host "  the steps - that part needs your account." -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
