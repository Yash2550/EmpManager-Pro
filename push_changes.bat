@echo off
echo ===================================================
echo  EmpManager Pro - Git Push & Deploy Script
echo ===================================================
echo.

:: Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in PATH.
    pause
    exit /b 1
)

:: Git Status
echo Current Git status:
git status -s
echo.

:: Confirm adding changes
set /p CONFIRM="Do you want to stage and commit all changes? (y/n): "
if /i "%CONFIRM%" neq "y" (
    echo Push cancelled.
    pause
    exit /b 0
)

:: Stage all changes
git add .

:: Prompt for commit message
set /p COMMIT_MSG="Enter commit message: "
if "%COMMIT_MSG%"=="" set COMMIT_MSG="Update code and configurations"

:: Commit changes
git commit -m "%COMMIT_MSG%"

:: Push changes
echo.
echo Pushing changes to remote repository...
git push origin main
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Direct push to 'main' failed. Trying active branch...
    for /f "tokens=*" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
    git push origin %CURRENT_BRANCH%
)

if %errorlevel% eq 0 (
    echo.
    echo [SUCCESS] Code pushed and updated successfully!
) else (
    echo.
    echo [ERROR] Push failed. Please check your remote repository settings or Git permissions.
)

pause
