cd "c:\Users\samee\OneDrive\Desktop\DREF ASSIST"
Remove-Item -Force -Recurse ".\.git\rebase-merge" -ErrorAction SilentlyContinue
Remove-Item -Force ".\.git\.COMMIT_EDITMSG.swp" -ErrorAction SilentlyContinue
Write-Host "Rebase cleaned up"
$env:GIT_EDITOR = "cmd /c exit 0"
git add -A
git rebase --continue --no-edit
if ($LASTEXITCODE -eq 0) {
    Write-Host "Rebase completed!"
    git push -f ifrcgo improvements/timeout-retry-ui-fixes
    Write-Host "Pushed to remote"
    git log --oneline -5
} else {
    Write-Host "Error: $LASTEXITCODE"
    git status
}
