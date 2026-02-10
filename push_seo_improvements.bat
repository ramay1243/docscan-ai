@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo Pushing SEO improvements to GitHub
echo ========================================
echo.

cd /d "C:\Users\Radmil\Desktop\docscan banner"
if errorlevel 1 (
    echo ERROR: Cannot change to project directory
    pause
    exit /b 1
)

if not exist "routes\main.py" (
    echo ERROR: Project files not found
    pause
    exit /b 1
)

echo Project directory: %CD%
echo.

echo [1/3] Checking git status...
git status --short
echo.

echo [2/3] Adding all changes and creating commit...
git add -A

git diff --cached --quiet 2>nul
if errorlevel 1 (
    git commit -m "SEO: Add 'Proverka dokumentov online' page, improve main page SEO, add internal linking for document checking keywords"
    
    if errorlevel 1 (
        echo ERROR: Failed to create commit
        git status
        pause
        exit /b 1
    )
    echo Commit created successfully.
) else (
    echo No changes to commit.
)

echo.
echo [3/3] Pushing to GitHub...
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


chcp 65001 >nul 2>&1

echo ========================================
echo Pushing SEO improvements to GitHub
echo ========================================
echo.

cd /d "C:\Users\Radmil\Desktop\docscan banner"
if errorlevel 1 (
    echo ERROR: Cannot change to project directory
    pause
    exit /b 1
)

if not exist "routes\main.py" (
    echo ERROR: Project files not found
    pause
    exit /b 1
)

echo Project directory: %CD%
echo.

echo [1/3] Checking git status...
git status --short
echo.

echo [2/3] Adding all changes and creating commit...
git add -A

git diff --cached --quiet 2>nul
if errorlevel 1 (
    git commit -m "SEO: Add 'Proverka dokumentov online' page, improve main page SEO, add internal linking for document checking keywords"
    
    if errorlevel 1 (
        echo ERROR: Failed to create commit
        git status
        pause
        exit /b 1
    )
    echo Commit created successfully.
) else (
    echo No changes to commit.
)

echo.
echo [3/3] Pushing to GitHub...
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

