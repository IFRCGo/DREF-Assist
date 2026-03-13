#!/usr/bin/env pwsh
<#
Script to complete the git rebase and resolve conflicts
#>

cd "c:\Users\samee\OneDrive\Desktop\DREF ASSIST"

Write-Host "Resolving rebase conflicts..."

# Add the resolved assistant.py file
Write-Host "1. Adding resolved assistant.py..."
& git add backend/services/assistant.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR adding assistant.py. Exit code: $LASTEXITCODE"
    exit 1
}

# Remove the .pyc conflict files (they're gitignored anyway)
Write-Host "2. Removing .pyc conflict files..."
& git rm -f "backend/conflict_resolver/__pycache__/__init__.cpython-312.pyc" 2>$null
& git rm -f "backend/conflict_resolver/__pycache__/detector.cpython-312.pyc" 2>$null
& git rm -f "backend/conflict_resolver/__pycache__/manager.cpython-312.pyc" 2>$null
& git rm -f "backend/conflict_resolver/__pycache__/service.cpython-312.pyc" 2>$null

# Continue the rebase
Write-Host "3. Continuing rebase with automatic editor..."
$env:GIT_EDITOR = "cmd /c exit 0"
& git rebase --continue --no-edit

if ($LASTEXITCODE -eq 0) {
    Write-Host "Rebase completed successfully!"
    Write-Host "4. Force pushing to remote..."
    & git push -f ifrcgo improvements/timeout-retry-ui-fixes
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully pushed to remote!"
        Write-Host ""
        Write-Host "Your branch is now 0 commits behind main."
        & git log --oneline -5
    }
} else {
    Write-Host "ERROR: Rebase continue failed with exit code: $LASTEXITCODE"
    exit 1
}
