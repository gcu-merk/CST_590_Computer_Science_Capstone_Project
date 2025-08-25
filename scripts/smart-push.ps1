param(
    [string]$Message,
    [switch]$DryRun,
    [switch]$Force,
    [switch]$All,
    [switch]$Interactive,
    [string]$Type,
    [string]$Scope,
    [string]$Branch
)

# Map command line shortcuts to full parameter names
$newArgs = @()
for ($i = 0; $i -lt $args.Count; $i++) {
    switch ($args[$i]) {
        "-dry" { $newArgs += "-DryRun" }
        "-b" { 
            $newArgs += "-Branch"
            if ($i + 1 -lt $args.Count) {
                $i++
                $newArgs += $args[$i]
            }
        }
        "-m" { 
            $newArgs += "-Message"
            if ($i + 1 -lt $args.Count) {
                $i++
                $newArgs += $args[$i]
            }
        }
        default { $newArgs += $args[$i] }
    }
}

# Re-parse with mapped arguments if we have any
if ($newArgs.Count -gt 0) {
    $params = @{}
    for ($i = 0; $i -lt $newArgs.Count; $i++) {
        switch ($newArgs[$i]) {
            "-DryRun" { $params["DryRun"] = $true }
            "-All" { $params["All"] = $true }
            "-Force" { $params["Force"] = $true }
            "-Interactive" { $params["Interactive"] = $true }
            "-Message" { 
                if ($i + 1 -lt $newArgs.Count) {
                    $i++
                    $params["Message"] = $newArgs[$i]
                }
            }
            "-Branch" { 
                if ($i + 1 -lt $newArgs.Count) {
                    $i++
                    $params["Branch"] = $newArgs[$i]
                }
            }
            "-Type" { 
                if ($i + 1 -lt $newArgs.Count) {
                    $i++
                    $params["Type"] = $newArgs[$i]
                }
            }
            "-Scope" { 
                if ($i + 1 -lt $newArgs.Count) {
                    $i++
                    $params["Scope"] = $newArgs[$i]
                }
            }
        }
    }
    
    # Override parameter values with parsed ones
    if ($params.ContainsKey("DryRun")) { $DryRun = $params["DryRun"] }
    if ($params.ContainsKey("All")) { $All = $params["All"] }
    if ($params.ContainsKey("Force")) { $Force = $params["Force"] }
    if ($params.ContainsKey("Interactive")) { $Interactive = $params["Interactive"] }
    if ($params.ContainsKey("Message")) { $Message = $params["Message"] }
    if ($params.ContainsKey("Branch")) { $Branch = $params["Branch"] }
    if ($params.ContainsKey("Type")) { $Type = $params["Type"] }
    if ($params.ContainsKey("Scope")) { $Scope = $params["Scope"] }
}

function Write-ColorOutput {
    param($Message, $Color = "White")
    switch ($Color) {
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Blue" { Write-Host $Message -ForegroundColor Blue }
        "Cyan" { Write-Host $Message -ForegroundColor Cyan }
        "Magenta" { Write-Host $Message -ForegroundColor Magenta }
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

function Get-GitStatus {
    $status = git status --porcelain
    $staged = @()
    $unstaged = @()
    $untracked = @()
    
    foreach ($line in $status) {
        if ($line -match '^[MADRC]') {
            $staged += $line.Substring(3)
        }
        if ($line -match '^.[MADRC]') {
            $unstaged += $line.Substring(3)
        }
        if ($line -match '^\?\?') {
            $untracked += $line.Substring(3)
        }
    }
    
    return @{
        Staged = $staged
        Unstaged = $unstaged
        Untracked = $untracked
        HasChanges = ($staged.Count -gt 0 -or $unstaged.Count -gt 0 -or $untracked.Count -gt 0)
    }
}

function Get-CommitType {
    param($Files)
    
    # Analyze file changes to suggest commit type
    $hasDocumentation = $Files | Where-Object { $_ -match '\.(md|txt|rst)$|docs/|README' }
    $hasTests = $Files | Where-Object { $_ -match 'test|spec' }
    $hasConfig = $Files | Where-Object { $_ -match '\.(json|yaml|yml|toml|ini|conf|config)$' }
    $hasCI = $Files | Where-Object { $_ -match '\.github/|\.yml$|\.yaml$|Dockerfile|docker-compose' }
    $hasPackage = $Files | Where-Object { $_ -match 'package\.json|requirements\.txt|setup\.py|pom\.xml' }
    $hasAssets = $Files | Where-Object { $_ -match '\.(css|scss|js|ts|png|jpg|jpeg|gif|svg)$' }
    
    if ($hasDocumentation) { return "docs" }
    if ($hasTests) { return "test" }
    if ($hasCI) { return "ci" }
    if ($hasConfig) { return "config" }
    if ($hasPackage) { return "deps" }
    if ($hasAssets) { return "style" }
    
    return "feat"  # Default to feature
}

function Get-CommitScope {
    param($Files)
    
    # Try to determine scope from file paths
    $commonPaths = @{}
    foreach ($file in $Files) {
        $parts = $file -split '[/\\]'
        if ($parts.Length -gt 1) {
            $topLevel = $parts[0]
            if ($commonPaths.ContainsKey($topLevel)) {
                $commonPaths[$topLevel]++
            } else {
                $commonPaths[$topLevel] = 1
            }
        }
    }
    
    if ($commonPaths.Count -gt 0) {
        $mostCommon = $commonPaths.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 1
        if ($mostCommon.Value -gt ($Files.Count / 2)) {
            return $mostCommon.Key
        }
    }
    
    return $null
}

function Get-AutoCommitMessage {
    param($Status)
    
    # Use all files for analysis (staged + what would be staged with -All)
    $allFiles = $Status.Staged + $Status.Unstaged + $Status.Untracked
    $filesToAnalyze = if ($Status.Staged.Count -gt 0) { $Status.Staged } else { $allFiles }
    
    # Determine commit type and scope
    $commitType = Get-CommitType -Files $filesToAnalyze
    $commitScope = Get-CommitScope -Files $filesToAnalyze
    
    # Generate description based on changes
    $description = ""
    $fileCount = $filesToAnalyze.Count
    
    if ($fileCount -eq 1) {
        $file = $filesToAnalyze[0]
        
        # Handle renamed files - use the new path
        $cleanFile = $file
        if ($file -match "(.+)\s*->\s*(.+)") {
            $cleanFile = $matches[2].Trim()
        }
        # Remove any leading status characters
        $cleanFile = $cleanFile -replace '^[AMDRC?!\s]+', ''
        
        $fileName = Split-Path $cleanFile -Leaf
        if ($cleanFile -match '\.(md|txt)$') {
            $description = "update $fileName documentation"
        } elseif ($cleanFile -match 'test') {
            $description = "add tests for $fileName"
        } elseif ($cleanFile -match '\.(js|ts|py|cs|java)$') {
            $description = "implement $fileName functionality"
        } else {
            $description = "update $fileName"
        }
    } elseif ($fileCount -le 5) {
        $fileTypes = $filesToAnalyze | ForEach-Object { 
            # Handle git status entries that may contain special characters or renames
            $cleanPath = $_
            if ($cleanPath -match "(.+)\s*->\s*(.+)") {
                # Handle renamed files - use the new path
                $cleanPath = $matches[2].Trim()
            }
            # Remove any leading status characters (A, M, D, etc.)
            $cleanPath = $cleanPath -replace '^[AMDRC?!\s]+', ''
            
            try {
                $ext = [System.IO.Path]::GetExtension($cleanPath)
                if ($ext) { $ext.TrimStart('.') } else { "file" }
            } catch {
                # If path extraction fails, try to get extension from filename
                if ($cleanPath -match '\.([^.]+)$') {
                    $matches[1]
                } else {
                    "file"
                }
            }
        } | Group-Object | Sort-Object Count -Descending
        
        if ($fileTypes -and $fileTypes.Count -gt 0) {
            $mainType = $fileTypes[0].Name
            if ($fileCount -eq 2) {
                $description = "update $fileCount $mainType files"
            } else {
                $description = "update multiple $mainType files"
            }
        } else {
            $description = "update $fileCount files"
        }
    } else {
        $description = "update $fileCount files"
    }
    
    # Build conventional commit message
    $message = $commitType
    if ($commitScope) {
        $message += "($commitScope)"
    }
    $message += ": $description"
    
    return $message
}

function Get-AutoBranchName {
    param($Status, $CommitType, $CommitScope)
    
    # Use all files for analysis (staged + what would be staged with -All)
    $allFiles = $Status.Staged + $Status.Unstaged + $Status.Untracked
    $filesToAnalyze = if ($Status.Staged.Count -gt 0) { $Status.Staged } else { $allFiles }
    
    # Generate branch name based on commit type and changes
    $branchName = $CommitType
    
    if ($CommitScope) {
        $branchName += "-$CommitScope"
    }
    
    # Add specific descriptor based on files
    $fileCount = $filesToAnalyze.Count
    
    if ($fileCount -eq 1) {
        $file = $filesToAnalyze[0]
        $fileName = Split-Path $file -LeafBase
        $cleanFileName = $fileName -replace '[^a-zA-Z0-9_-]', '-'
        $branchName += "-$cleanFileName"
    } elseif ($fileCount -le 5) {
        $fileTypes = $filesToAnalyze | ForEach-Object { 
            $ext = [System.IO.Path]::GetExtension($_)
            if ($ext) { $ext.TrimStart('.') } else { "file" }
        } | Group-Object | Sort-Object Count -Descending
        
        if ($fileTypes -and $fileTypes.Count -gt 0) {
            $mainType = $fileTypes[0].Name
            $branchName += "-$mainType-updates"
        } else {
            $branchName += "-multiple-files"
        }
    } else {
        $branchName += "-batch-update"
    }
    
    # Add timestamp to ensure uniqueness
    $timestamp = Get-Date -Format "MMdd"
    $branchName += "-$timestamp"
    
    # Clean up branch name (replace invalid characters)
    $branchName = $branchName -replace '[^a-zA-Z0-9_/-]', '-'
    $branchName = $branchName -replace '-+', '-'
    $branchName = $branchName.Trim('-')
    
    return $branchName
}

function Show-CommitPreview {
    param($Message, $Status)
    
    Write-Header "COMMIT PREVIEW"
    Write-ColorOutput "Commit message: $Message" "Yellow"
    Write-Host ""
    
    if ($Status.Staged.Count -gt 0) {
        Write-ColorOutput "Staged files:" "Green"
        foreach ($file in $Status.Staged) {
            Write-ColorOutput "  + $file" "Green"
        }
        Write-Host ""
    }
    
    if ($Status.Unstaged.Count -gt 0) {
        Write-ColorOutput "Unstaged files (will be added with -All):" "Yellow"
        foreach ($file in $Status.Unstaged) {
            Write-ColorOutput "  M $file" "Yellow"
        }
        Write-Host ""
    }
    
    if ($Status.Untracked.Count -gt 0) {
        Write-ColorOutput "Untracked files (will be added with -All):" "Red"
        foreach ($file in $Status.Untracked) {
            Write-ColorOutput "  ? $file" "Red"
        }
        Write-Host ""
    }
}

function Get-InteractiveCommitMessage {
    Write-Header "INTERACTIVE COMMIT MESSAGE"
    
    # Suggest commit types
    Write-ColorOutput "Conventional commit types:" "Cyan"
    Write-Host "  feat     - A new feature"
    Write-Host "  fix      - A bug fix"
    Write-Host "  docs     - Documentation changes"
    Write-Host "  style    - Code style changes (formatting, etc.)"
    Write-Host "  refactor - Code refactoring"
    Write-Host "  test     - Adding or updating tests"
    Write-Host "  chore    - Maintenance tasks"
    Write-Host "  ci       - CI/CD changes"
    Write-Host "  deps     - Dependency updates"
    Write-Host ""
    
    $type = Read-Host "Enter commit type (or press Enter for auto-detection)"
    if (-not $type) { $type = "" }
    
    $scope = Read-Host "Enter scope (optional, e.g., 'auth', 'ui', 'api')"
    if (-not $scope) { $scope = "" }
    
    $description = Read-Host "Enter description"
    while (-not $description) {
        Write-ColorOutput "Description is required!" "Red"
        $description = Read-Host "Enter description"
    }
    
    # Build message
    if ($type) {
        $message = $type
        if ($scope) {
            $message += "($scope)"
        }
        $message += ": $description"
    } else {
        $message = $description
    }
    
    # Ask for breaking change
    $breakingChange = Read-Host "Is this a breaking change? (y/N)"
    if ($breakingChange -eq "y" -or $breakingChange -eq "Y") {
        $message = $message.Replace(":", "!:")
    }
    
    return $message
}

Write-Header "GIT SMART PUSH TOOL"

# Verify we're in a Git repository
if (-not (Test-Path ".git")) {
    Write-ColorOutput "ERROR: Not a Git repository. Please run this script from the root of your Git project." "Red"
    exit 1
}

# Get current branch
$currentBranch = (git branch --show-current).Trim()
Write-ColorOutput "Current branch: $currentBranch" "Blue"

# Get git status
$status = Get-GitStatus

if (-not $status.HasChanges) {
    Write-ColorOutput "No changes to commit. Repository is clean." "Green"
    
    # Check if we need to push existing commits
    $unpushedCommits = git log origin/$currentBranch..$currentBranch --oneline 2>$null
    if ($unpushedCommits) {
        Write-ColorOutput "Found unpushed commits:" "Yellow"
        foreach ($commit in $unpushedCommits) {
            Write-ColorOutput "  $commit" "Yellow"
        }
        Write-Host ""
        $pushOnly = Read-Host "Push existing commits? (y/N)"
        if ($pushOnly -eq "y" -or $pushOnly -eq "Y") {
            if ($DryRun) {
                Write-ColorOutput "DRY RUN: Would push to origin/$currentBranch" "Yellow"
            } else {
                Write-ColorOutput "Pushing to origin/$currentBranch..." "Blue"
                git push origin $currentBranch
                if ($LASTEXITCODE -eq 0) {
                    Write-ColorOutput "Successfully pushed!" "Green"
                } else {
                    Write-ColorOutput "Push failed!" "Red"
                    exit 1
                }
            }
        }
    } else {
        Write-ColorOutput "Repository is up to date with remote." "Green"
    }
    exit 0
}

# Show current status
Write-Header "REPOSITORY STATUS"
Write-ColorOutput "Staged files: $($status.Staged.Count)" "Green"
Write-ColorOutput "Unstaged files: $($status.Unstaged.Count)" "Yellow"
Write-ColorOutput "Untracked files: $($status.Untracked.Count)" "Red"
Write-Host ""

# Handle -All flag
if ($All) {
    Write-ColorOutput "Adding all changes..." "Blue"
    if (-not $DryRun) {
        git add -A
        $status = Get-GitStatus  # Refresh status
    }
}

# Ensure we have staged changes
if ($status.Staged.Count -eq 0 -and -not $All) {
    Write-ColorOutput "No staged changes. Use -All to stage all changes, or stage files manually." "Yellow"
    Write-Host ""
    $stageAll = Read-Host "Stage all changes? (Y/n)"
    if ($stageAll -eq "n" -or $stageAll -eq "N") {
        Write-ColorOutput "Please stage your changes and run again." "Yellow"
        exit 0
    } else {
        Write-ColorOutput "Adding all changes..." "Blue"
        if (-not $DryRun) {
            git add -A
            $status = Get-GitStatus  # Refresh status
        }
    }
}

# Determine commit message
if ($Interactive) {
    $commitMessage = Get-InteractiveCommitMessage
} elseif ($Message) {
    $commitMessage = $Message
} else {
    $commitMessage = Get-AutoCommitMessage -Status $status
    Write-ColorOutput "Auto-generated commit message: $commitMessage" "Cyan"
    Write-Host ""
    
    $useAuto = Read-Host "Use this message? (Y/n/e to edit)"
    if ($useAuto -eq "n" -or $useAuto -eq "N") {
        $commitMessage = Read-Host "Enter custom commit message"
    } elseif ($useAuto -eq "e" -or $useAuto -eq "E") {
        $commitMessage = Get-InteractiveCommitMessage
    }
}

# Create new branch if we're on main/master
if ($currentBranch -eq "main" -or $currentBranch -eq "master") {
    if ($Branch) {
        $newBranch = $Branch
        Write-Host ""
        Write-ColorOutput "Creating custom branch: $newBranch" "Magenta"
    } else {
        $allFiles = $status.Staged + $status.Unstaged + $status.Untracked
        $filesToAnalyze = if ($status.Staged.Count -gt 0) { $status.Staged } else { $allFiles }
        $commitType = Get-CommitType -Files $filesToAnalyze
        $commitScope = Get-CommitScope -Files $filesToAnalyze
        
        $newBranch = Get-AutoBranchName -Status $status -CommitType $commitType -CommitScope $commitScope
        
        Write-Host ""
        Write-ColorOutput "Creating auto-generated branch: $newBranch" "Magenta"
    }
    
    if (-not $DryRun) {
        git checkout -b $newBranch
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "Failed to create branch. Exiting." "Red"
            exit 1
        }
        $currentBranch = $newBranch
        Write-ColorOutput "Switched to new branch: $newBranch" "Green"
    } else {
        Write-ColorOutput "DRY RUN: Would create and checkout branch: $newBranch" "Yellow"
        $currentBranch = $newBranch  # For dry run display purposes
    }
    Write-Host ""
}

# Show preview
Show-CommitPreview -Message $commitMessage -Status $status

# Confirmation
if (-not $DryRun) {
    $confirm = Read-Host "Proceed with commit and push? (Y/n)"
    if ($confirm -eq "n" -or $confirm -eq "N") {
        Write-ColorOutput "Operation cancelled." "Yellow"
        exit 0
    }
}

# Perform operations
Write-Header "EXECUTING OPERATIONS"

if ($DryRun) {
    Write-ColorOutput "DRY RUN: Would commit with message: $commitMessage" "Yellow"
    Write-ColorOutput "DRY RUN: Would push to origin/$currentBranch" "Yellow"
} else {
    # Commit
    Write-ColorOutput "Committing changes..." "Blue"
    git commit -m $commitMessage
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Commit failed!" "Red"
        exit 1
    }
    
    # Push
    Write-ColorOutput "Pushing to origin/$currentBranch..." "Blue"
    if ($Force) {
        git push origin $currentBranch --force-with-lease
    } else {
        git push origin $currentBranch
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Header "SUCCESS"
        Write-ColorOutput "Successfully committed and pushed!" "Green"
        Write-ColorOutput "Commit: $commitMessage" "Cyan"
        Write-ColorOutput "Branch: $currentBranch" "Cyan"
    } else {
        Write-ColorOutput "Push failed!" "Red"
        exit 1
    }
}
