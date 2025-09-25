@echo off
REM Git Smart Push - Easy Access Script
REM Usage: smart-push [options]

set "scriptPath=%~dp0scripts\smart-push.ps1"

REM Check for help
if /i "%~1"=="-help" goto show_help
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="help" goto show_help

REM Pass all arguments directly to PowerShell
powershell -ExecutionPolicy RemoteSigned -File "%scriptPath%" %*
goto end

:show_help
echo.
echo Git Smart Push Tool
echo ==================
echo.
echo Usage: smart-push [options]
echo.
echo Options:
echo   [none]                      Auto-detect commit message and push
echo   -dry                        Preview what would be committed and pushed
echo   -all                        Stage all changes before committing
echo   -interactive                Interactive commit message creation
echo   -force                      Force push with lease (dangerous!)
echo   -message "msg" / -m "msg"   Custom commit message
echo   -branch "name" / -b "name"  Custom branch name (if creating new branch)
echo   -type "type"                Force commit type (feat, fix, docs, etc.)
echo   -scope "scope"              Force commit scope
echo   -help / -h                  Show this help message
echo.
echo Examples:
echo   smart-push                           Auto-commit and push
echo   smart-push -dry                      Preview changes
echo   smart-push -all                      Stage all changes and push
echo   smart-push -interactive              Interactive commit message
echo   smart-push -m "fix: bug in parser"   Custom commit message
echo   smart-push -b "feature/new-api"      Create custom branch name
echo.
echo Branch Creation:
echo   - Automatically creates feature branches when on main/master
echo   - Generates descriptive branch names based on changes
echo   - Supports custom branch names with -branch option
echo.
echo Commit Message Features:
echo   - Auto-generates conventional commit messages
echo   - Analyzes file changes to suggest commit type
echo   - Supports interactive message creation
echo   - Follows conventional commit format
echo.

:end
