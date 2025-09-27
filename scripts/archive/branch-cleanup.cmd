@echo off
REM Git Branch Cleanup - Easy Access Script
REM Usage: branch-cleanup [options]
REM   -dry        Preview what would be cleaned up
REM   -keep       Keep develop branch
REM   -force      Force delete unmerged branches

set "scriptPath=%~dp0scripts\branch-cleanup.ps1"

if "%1"=="-dry" (
    powershell -ExecutionPolicy RemoteSigned -File "%scriptPath%" -DryRun
) else if "%1"=="-keep" (
    powershell -ExecutionPolicy RemoteSigned -File "%scriptPath%" -KeepDevelop
) else if "%1"=="-force" (
    powershell -ExecutionPolicy RemoteSigned -File "%scriptPath%" -Force
) else if "%1"=="-help" (
    echo.
    echo Git Branch Cleanup Tool
    echo =====================
    echo.
    echo Usage: branch-cleanup [option]
    echo.
    echo Options:
    echo   [none]      Standard cleanup of merged branches
    echo   -dry        Preview what would be cleaned up
    echo   -keep       Keep develop branch during cleanup
    echo   -force      Force delete unmerged branches (dangerous^)
    echo   -help       Show this help message
    echo.
    echo Examples:
    echo   branch-cleanup           Standard cleanup
    echo   branch-cleanup -dry      Preview cleanup
    echo   branch-cleanup -keep     Keep develop branch
    echo.
) else (
    powershell -ExecutionPolicy RemoteSigned -File "%scriptPath%"
)
