# Puts this project under version control and makes the first commit.
#
# Nothing is uploaded anywhere. This is entirely local: it creates the repo,
# checks that no secret is about to be committed, and commits. Pushing to
# GitHub is a separate, deliberate step you do afterwards.
#
# Note on error handling: git writes ordinary status to stderr and returns a
# non-zero exit code for perfectly normal conditions - "this repo has no
# commits yet" being one. So we check $LASTEXITCODE deliberately rather than
# letting PowerShell treat every stderr line as fatal.

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Say($text, $color = "White") { Write-Host "  $text" -ForegroundColor $color }

function Test-Git([scriptblock] $block) {
    & $block *>$null
    return $LASTEXITCODE -eq 0
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  NEXA - set up version control" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# --- git present? ---------------------------------------------------------
$version = git --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Say "[X] Git is not installed." Red
    Say "    Get it from https://git-scm.com/download/win, install with the" DarkGray
    Say "    default options, then run this again." DarkGray
    exit 1
}
Say "$version detected." Green

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
    Say "Commits authored by $name <$email>"
}

# --- init -----------------------------------------------------------------
if (Test-Path ".git") {
    Say "Repository already exists here."
} else {
    git init -b main *>$null
    if ($LASTEXITCODE -ne 0) { Say "[X] git init failed." Red; exit 1 }
    Say "Repository created (branch: main)." Green
}

# Quieten the line-ending warnings before anything is staged.
git config core.autocrlf true *>$null

# --- stage ----------------------------------------------------------------
git add -A *>$null
$staged = @(git diff --cached --name-only)

# --- safety: nothing secret may be committed ------------------------------
$danger = $staged | Where-Object {
    $_ -match '(^|/)\.env$' -or
    $_ -match '\.env\.(local|production)$' -or
    $_ -match '\.pem$' -or
    $_ -match '\.key$'
}
if ($danger) {
    Write-Host ""
    Say "[X] STOPPING - these would be committed and must not be:" Red
    $danger | ForEach-Object { Say "      $_" Red }
    Say "    Nothing was committed. Check .gitignore." DarkGray
    git reset *>$null
    exit 1
}
Say "Safety check passed - no .env or key files staged." Green

if (Test-Git { git check-ignore backend/.env }) {
    Say "backend\.env is correctly ignored by git." Green
} else {
    Say "[!] backend\.env is NOT ignored. Stopping. Tell Claude." Red
    git reset *>$null
    exit 1
}

Say "$($staged.Count) files staged."

# --- commit ---------------------------------------------------------------
# An empty repo has no HEAD; that is a normal state, not an error.
$hasCommits = Test-Git { git rev-parse --verify HEAD }

if ($hasCommits) {
    if ($staged.Count -eq 0) {
        Say "Nothing changed since the last commit." Yellow
    } else {
        git commit -m "Update NEXA AI Analyzer" *>$null
        if ($LASTEXITCODE -ne 0) { Say "[X] Commit failed." Red; exit 1 }
        Say "Committed $($staged.Count) changed files." Green
    }
} else {
    $message = @"
Initial commit: NEXA AI Analyzer

Backend (FastAPI):
- Centralised config, structured logging, framework-free domain errors
- Document pipeline: PDF/DOCX/TXT extraction, section, bullet and contact detection
- AI layer: provider interface (Anthropic + Gemini), schema-validated structured
  output, informed retry on invalid responses, transient-outage retry, content cache
- Analysis module registry with four modules: resume analysis, job match,
  ATS analysis, career intelligence
- 44 tests, no network calls or API key required

Frontend (Next.js 15 + TypeScript + Tailwind):
- Dashboard with upload, job description, module selection
- One result view per module, mapped through a frontend registry
- Loading, empty and error states; provider-aware error hints
"@
    git commit -m $message *>$null
    if ($LASTEXITCODE -ne 0) { Say "[X] Commit failed." Red; exit 1 }
    Say "First commit created." Green
}

Write-Host ""
git --no-pager log --oneline -5
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Done. Your work now has history and undo." -ForegroundColor Cyan
Write-Host "  Next: GitHub - tell Claude when you're ready." -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
