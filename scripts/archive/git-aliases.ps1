# Git Branch Cleanup Functions
# Add these to your PowerShell profile for easy access

function Invoke-BranchCleanup {
    <#
    .SYNOPSIS
        Quick alias for git branch cleanup
    .DESCRIPTION
        Runs the branch cleanup script with various options
    .PARAMETER DryRun
        Preview what would be cleaned up
    .PARAMETER Force
        Force delete unmerged branches
    .PARAMETER KeepDevelop
        Keep develop branch even if merged
    .EXAMPLE
        branch-cleanup
        Standard cleanup
    .EXAMPLE
        branch-cleanup -DryRun
        Preview cleanup
    #>
    param(
        [switch]$DryRun,
        [switch]$Force,
        [switch]$KeepDevelop
    )
    
    $scriptPath = Join-Path $PWD "scripts\branch-cleanup.ps1"
    
    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ Branch cleanup script not found at: $scriptPath" -ForegroundColor Red
        Write-Host "💡 Make sure you're in the project root directory" -ForegroundColor Yellow
        return
    }
    
    & $scriptPath @PSBoundParameters
}

# Create aliases for convenience
Set-Alias -Name "branch-cleanup" -Value Invoke-BranchCleanup
Set-Alias -Name "cleanup-branches" -Value Invoke-BranchCleanup
Set-Alias -Name "git-cleanup" -Value Invoke-BranchCleanup

# Quick functions for common scenarios
function cleanup-dry { Invoke-BranchCleanup -DryRun }
function cleanup-keep-develop { Invoke-BranchCleanup -KeepDevelop }
function cleanup-force { Invoke-BranchCleanup -Force }

Write-Host "🧹 Git Branch Cleanup functions loaded!" -ForegroundColor Green
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  • branch-cleanup          - Clean up merged branches" -ForegroundColor Blue
Write-Host "  • branch-cleanup -DryRun  - Preview cleanup" -ForegroundColor Blue
Write-Host "  • cleanup-dry             - Quick dry run" -ForegroundColor Blue
Write-Host "  • cleanup-keep-develop    - Keep develop branch" -ForegroundColor Blue
Write-Host "  • cleanup-force           - Force delete branches" -ForegroundColor Blue
