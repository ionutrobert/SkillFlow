@echo off
setlocal enabledelayedexpansion

:menu
cls
type banner.txt
echo.
echo =====================================================
echo   Smart Skill Organization for AI Agents
echo.
echo =====================================================
echo.
echo   Choose an operation:
echo.
echo   1. Dry Run (Preview changes)
echo   2. Run Full Setup (Migrate)
echo   3. Show Statistics
echo   4. Check Health Status
echo   5. Revert Migration
echo   6. Optimize Categorization
echo   7. Sync New Skills
echo   8. Exit
echo.
set /p choice=Select 1-8: 

if "%choice%"=="1" goto dryrun
if "%choice%"=="2" goto migrate
if "%choice%"=="3" goto stats
if "%choice%"=="4" goto status
if "%choice%"=="5" goto revert
if "%choice%"=="6" goto optimize
if "%choice%"=="7" goto sync
if "%choice%"=="8" exit /b 0
goto menu

:dryrun
cls
echo.
echo Running Dry Run Preview...
echo.
py setup.py --dry-run
echo.
pause
goto menu

:migrate
cls
echo.
echo Running Full Setup...
echo.
py setup.py
echo.
pause
goto menu

:stats
cls
echo.
echo Showing Statistics...
echo.
py setup.py --stats
echo.
pause
goto menu

:status
cls
echo.
echo Checking Health Status...
echo.
py setup.py --status
echo.
pause
goto menu

:revert
cls
echo.
echo Reverting Migration...
echo.
py setup.py --revert
echo.
pause
goto menu

:optimize
cls
echo.
echo Optimizing Categorization...
echo.
py setup.py --optimize
echo.
pause
goto menu

:sync
cls
echo.
echo Syncing New Skills...
echo.
py setup.py --sync
echo.
pause
goto menu
