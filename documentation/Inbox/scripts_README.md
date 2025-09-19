# Scripts Directory

This directory contains automation scripts for common development tasks.

## 🧹 Branch Cleanup Script

### ⚡ Quick Start (Easiest Method)

```cmd
# From project root directory
branch-cleanup -dry    # Preview cleanup
branch-cleanup         # Standard cleanup
branch-cleanup -keep   # Keep develop branch
branch-cleanup -help   # Show help
```

### 🔧 PowerShell Method

```powershell
# From project root directory
.\scripts\branch-cleanup.ps1 -DryRun
.\scripts\branch-cleanup.ps1
.\scripts\branch-cleanup.ps1 -KeepDevelop
```

### 🎯 Features

- ✅ **Safe Cleanup**: Only removes branches merged into `main`
- 🔍 **Dry Run Mode**: Preview changes before executing  
- 🌐 **Remote Support**: Cleans both local and remote branches
- 🔒 **Flexible Options**: Keep specific branches like `develop`
- 🎨 **Colorized Output**: Clear, readable feedback
- ⚡ **Fast**: Efficient Git operations
- 🚀 **Easy Access**: Simple command-line interface

### 📋 Usage Examples

#### Command Line Interface (Recommended)

```cmd
# Preview what would be cleaned (always recommended first)
branch-cleanup -dry

# Standard cleanup of merged branches
branch-cleanup

# Keep develop branch during cleanup  
branch-cleanup -keep

# Force delete unmerged branches (use with caution)
branch-cleanup -force

# Show help and options
branch-cleanup -help
```

#### PowerShell Direct Usage

```powershell
# Preview cleanup
.\scripts\branch-cleanup.ps1 -DryRun

# Standard cleanup
.\scripts\branch-cleanup.ps1

# Keep develop branch
.\scripts\branch-cleanup.ps1 -KeepDevelop

# Force delete unmerged branches
.\scripts\branch-cleanup.ps1 -Force

# Combine options
.\scripts\branch-cleanup.ps1 -DryRun -KeepDevelop
```

### 🛡️ Safety Features

- ❌ **Prevents accidents**: Won't delete `main` or current branch
- ✅ **Confirmation prompt**: Asks before making changes (unless dry run)
- 🔍 **Verification**: Checks if branches actually exist before deletion
- 📊 **Status report**: Shows final repository state
- ⚠️ **Error handling**: Graceful failure with helpful messages

### 🔄 What It Does

1. **Verifies** you're in a Git repository
2. **Switches** to `main` branch if needed  
3. **Updates** `main` from remote
4. **Identifies** branches merged into `main`
5. **Shows** what will be cleaned up
6. **Confirms** with user (unless dry run)
7. **Removes** local merged branches
8. **Removes** remote merged branches (if they exist)
9. **Prunes** stale remote tracking references
10. **Reports** final repository status

### 🔗 Integration with CI/CD

This script complements the established branching strategy:

- **Feature branches** → Automatically cleaned after merge to `main`
- **`develop` branch** → Optionally preserved for ongoing integration  
- **`main` branch** → Never touched, always protected

### 🚨 Troubleshooting

- **"Not a Git repository"**: Run from project root
- **"Failed to delete"**: Branch may have unmerged changes, use `-force` if needed
- **"Remote ref does not exist"**: Remote branch already deleted, script will continue
- **"Execution policy"**: Script automatically sets RemoteSigned policy

### 💡 Pro Tips

1. **Always use dry run first**: `branch-cleanup -dry`
2. **Keep develop for active projects**: `branch-cleanup -keep`  
3. **Run after merging PRs**: Keep repository clean
4. **Check status**: Script shows final repository state
5. **Use from anywhere**: Works from project root directory

---

## 📁 Files Structure

```text
scripts/
├── branch-cleanup.ps1      # Main PowerShell script
├── git-aliases.ps1         # PowerShell aliases (optional)
└── README.md              # This documentation

# Easy access from scripts folder:
scripts/branch-cleanup.cmd  # Command-line interface
```

---

## 🔧 Adding New Scripts

When adding new automation scripts:

1. Create the script in this directory
2. Add documentation to this README
3. Consider adding a command-line interface like `scripts/branch-cleanup.cmd`
4. Test thoroughly before committing
5. Follow PowerShell best practices
