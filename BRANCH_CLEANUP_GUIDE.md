# 🧹 Quick Branch Cleanup

## Super Easy Method

Just run this from your project root:

```cmd
branch-cleanup -dry    # Preview what will be cleaned
branch-cleanup         # Clean up merged branches
```

## What It Does

- ✅ Removes branches that have been merged into `main`  
- 🛡️ Never touches `main` or your current branch
- 🌐 Cleans both local and remote branches
- 📊 Shows you what it's doing every step

## Options

```cmd
branch-cleanup -dry     # Preview only (recommended first)
branch-cleanup          # Standard cleanup
branch-cleanup -keep    # Keep develop branch
branch-cleanup -force   # Force delete unmerged branches
branch-cleanup -help    # Show all options
```

## Safe to Use

- Always previews changes first with `-dry`
- Asks for confirmation before deleting anything
- Only removes branches that are already merged
- Shows final repository status when done

For more details, see [scripts/README.md](scripts/README.md)
