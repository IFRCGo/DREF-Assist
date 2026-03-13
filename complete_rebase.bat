@echo off
setlocal enabledelayedexpansion

cd /d "c:\Users\samee\OneDrive\Desktop\DREF ASSIST"

echo Adding all files...
git add -A

echo Continuing rebase...
set GIT_EDITOR=cmd /c exit 0
git rebase --continue --no-edit

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Rebase completed successfully!
    echo.
    echo Pushing to remote...
    git push -f ifrcgo improvements/timeout-retry-ui-fixes
    
    if %ERRORLEVEL% EQU 0 (
        echo Push successful!
        echo.
        git log --oneline -5
    ) else (
        echo Push failed with error code !ERRORLEVEL!
    )
) else (
    echo Rebase failed with error code !ERRORLEVEL!
    echo Running: git status
    git status
)

pause
