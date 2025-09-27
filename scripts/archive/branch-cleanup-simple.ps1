param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$KeepDevelop
)

function Write-ColorOutput {
    param($Message, $Color = "White")
    switch ($Color) {
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Blue" { Write-Host $Message -ForegroundColor Blue }
        "Cyan" { Write-Host $Message -ForegroundColor Cyan }
        default { Write-Host $Message }
    }
}

function Write-Header {
    param($Title)
    Write-Host ""
    Write-ColorOutput "=================================================================" "Cyan"
    Write-ColorOutput "  $Title" "Cyan"
    Write-ColorOutput "=================================================================" "Cyan"
    Write-Host ""
}

Write-Header "GIT BRANCH CLEANUP TOOL"

# Verify we're in a Git repository
if (-not (Test-Path ".git")) {
    Write-ColorOutput "ERROR: Not a Git repository. Please run this script from the root of your Git project." "Red"
    exit 1
}

# Check current branch
$currentBranch = (git branch --show-current).Trim()
Write-ColorOutput "Current branch: $currentBranch" "Blue"

if ($currentBranch -ne "main") {
    Write-ColorOutput "WARNING: You're not on the main branch. Switching to main..." "Yellow"
    git checkout main
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "ERROR: Failed to switch to main branch. Please switch manually and try again." "Red"
        exit 1
    }
}

# Update main branch
Write-ColorOutput "Updating main branch..." "Blue"
git pull origin main --quiet

# Build exclusion list
$excludeBranches = @()
if ($KeepDevelop) {
    $excludeBranches += "develop"
    Write-ColorOutput "Keeping develop branch as requested" "Yellow"
}

# Get merged local branches
$localMerged = @()
$branches = git branch --merged main

foreach ($branch in $branches) {
    $cleanBranch = $branch.Trim().Replace("* ", "")
    if ($cleanBranch -ne "main" -and $cleanBranch -notin $excludeBranches) {
        $localMerged += $cleanBranch
    }
}

# Get merged remote branches
$remoteMerged = @()
$remoteBranches = git branch -r --merged main

foreach ($branch in $remoteBranches) {
    $cleanBranch = $branch.Trim()
    if ($cleanBranch -notmatch "origin/HEAD" -and $cleanBranch -ne "origin/main") {
        $branchName = $cleanBranch -replace "origin/", ""
        if ($branchName -notin $excludeBranches) {
            $remoteMerged += $branchName
        }
    }
}

# Show what will be cleaned up
Write-Header "ANALYSIS RESULTS"

if ($localMerged.Count -eq 0 -and $remoteMerged.Count -eq 0) {
    Write-ColorOutput "Repository is already clean! No merged branches to remove." "Green"
    Write-Header "REPOSITORY STATUS"
    Write-ColorOutput "Local branches:" "Blue"
    git branch | ForEach-Object { Write-ColorOutput "  $_" "Blue" }
    Write-Host ""
    Write-ColorOutput "Remote branches:" "Blue"
    git branch -r | ForEach-Object { Write-ColorOutput "  $_" "Blue" }
    exit 0
}

if ($localMerged.Count -gt 0) {
    Write-ColorOutput "Local branches merged into main:" "Yellow"
    foreach ($branch in $localMerged) {
        Write-ColorOutput "  - $branch" "Yellow"
    }
} else {
    Write-ColorOutput "No local branches to clean up" "Green"
}

Write-Host ""

if ($remoteMerged.Count -gt 0) {
    Write-ColorOutput "Remote branches merged into main:" "Yellow"
    foreach ($branch in $remoteMerged) {
        Write-ColorOutput "  - origin/$branch" "Yellow"
    }
} else {
    Write-ColorOutput "No remote branches to clean up" "Green"
}

# Confirmation prompt (unless dry run)
if (-not $DryRun) {
    Write-Host ""
    $confirmation = Read-Host "Do you want to proceed with cleanup? (y/N)"
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-ColorOutput "Cleanup cancelled by user" "Yellow"
        exit 0
    }
}

# Perform cleanup
Write-Header "CLEANING UP BRANCHES"

# Remove local branches
Write-ColorOutput "Removing local branches..." "Blue"
if ($localMerged.Count -eq 0) {
    Write-ColorOutput "  No local branches to clean up" "Green"
} else {
    foreach ($branch in $localMerged) {
        if ($DryRun) {
            Write-ColorOutput "  Would delete local branch: $branch" "Yellow"
        } else {
            $deleteFlag = if ($Force) { "-D" } else { "-d" }
            $result = git branch $deleteFlag $branch 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "  Deleted local branch: $branch" "Green"
            } else {
                Write-ColorOutput "  Failed to delete local branch $branch : $result" "Red"
            }
        }
    }
}

Write-Host ""

# Remove remote branches
Write-ColorOutput "Removing remote branches..." "Blue"
if ($remoteMerged.Count -eq 0) {
    Write-ColorOutput "  No remote branches to clean up" "Green"
} else {
    # First, check which remote branches actually exist
    $existingRemotes = @()
    $remoteHeads = git ls-remote --heads origin
    
    foreach ($branch in $remoteMerged) {
        if ($remoteHeads -match "refs/heads/$branch") {
            $existingRemotes += $branch
        }
    }
    
    if ($existingRemotes.Count -eq 0) {
        Write-ColorOutput "  Remote branches already cleaned up" "Green"
    } else {
        foreach ($branch in $existingRemotes) {
            if ($DryRun) {
                Write-ColorOutput "  Would delete remote branch: origin/$branch" "Yellow"
            } else {
                $result = git push origin --delete $branch 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-ColorOutput "  Deleted remote branch: origin/$branch" "Green"
                } else {
                    Write-ColorOutput "  Failed to delete remote branch $branch : $result" "Yellow"
                }
            }
        }
    }
}

Write-Host ""

# Prune stale remote references
Write-ColorOutput "Pruning stale remote references..." "Blue"
if ($DryRun) {
    Write-ColorOutput "  Would prune stale remote tracking branches" "Yellow"
} else {
    $result = git remote prune origin 2>&1
    Write-ColorOutput "  Pruned stale remote tracking branches" "Green"
    if ($result -and $result -notmatch "nothing to prune") {
        Write-ColorOutput "     $result" "Blue"
    }
}

# Final status
if (-not $DryRun) {
    Write-Header "REPOSITORY STATUS"
    
    $currentBranch = (git branch --show-current).Trim()
    Write-ColorOutput "Current branch: $currentBranch" "Green"
    Write-Host ""
    
    Write-ColorOutput "Local branches:" "Blue"
    git branch | ForEach-Object { Write-ColorOutput "  $_" "Blue" }
    Write-Host ""
    
    Write-ColorOutput "Remote branches:" "Blue"
    git branch -r | ForEach-Object { Write-ColorOutput "  $_" "Blue" }
    
    Write-Header "CLEANUP COMPLETE"
    Write-ColorOutput "Branch cleanup completed successfully!" "Green"
} else {
    Write-Header "DRY RUN COMPLETE"
    Write-ColorOutput "Use without -DryRun to actually perform the cleanup" "Blue"
}
