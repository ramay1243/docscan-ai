@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo Pushing analysis improvements to GitHub
echo ========================================
echo.

cd /d "C:\Users\Radmil\Desktop\docscan banner"
if errorlevel 1 (
    echo ERROR: Cannot change to project directory
    pause
    exit /b 1
)

if not exist "routes\api.py" (
    echo ERROR: Project files not found
    pause
    exit /b 1
)

echo Project directory: %CD%
echo.

echo [1/4] Checking for uncommitted changes...
git add -A
git diff --cached --quiet 2>nul
set HAS_UNCOMMITTED=%errorlevel%

if %HAS_UNCOMMITTED%==0 (
    echo No changes to commit.
    echo [2/4] Skipping commit.
    git reset
) else (
    echo Changes found, files staged...
    
    if errorlevel 1 (
        echo ERROR: Failed to add files
        pause
        exit /b 1
    )
    
    echo.
    echo [2/4] Creating commit...
    git commit -m "SEO: Add 'Proverka dokumentov online' page, improve main page SEO, add internal linking for document checking keywords"
    
    if errorlevel 1 (
        echo ERROR: Failed to create commit
        git status
        git reset
        pause
        exit /b 1
    )
    echo Commit created successfully.
)

echo.
echo [3/4] Checking if there are commits to push...
git log origin/main..HEAD --oneline >nul 2>&1
if errorlevel 1 (
    echo No commits to push. Everything is up to date.
    echo.
    echo ========================================
    echo Success! Repository is up to date
    echo ========================================
    pause
    exit /b 0
)

echo.
echo [4/4] Pushing to GitHub...
git push origin main

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Failed to push to GitHub
    echo ========================================
    echo.
    echo You may need to run manually: git push origin main
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo Success! Changes pushed to GitHub
    echo ========================================
)

echo.
pause
