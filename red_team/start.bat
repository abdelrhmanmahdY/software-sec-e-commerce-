@echo off
setlocal enabledelayedexpansion
REM SecureShop Red Team — convenience menu.
REM Run this from anywhere; it switches to the project root itself.
cd /d "%~dp0\.."

:menu
echo.
echo ============================================
echo  SecureShop Red Team
echo ============================================
echo  1. Start SecureShop (Docker: db + web + nginx)
echo  2. Re-run live regression tests against SecureShop
echo  3. Start the Naive Shop and run attacks against it
echo  4. Run Bandit + pip-audit (static analysis)
echo  5. Rebuild HTML reports
echo  6. Open the reports index in your browser
echo  7. Stop SecureShop (docker compose down)
echo  0. Exit
echo ============================================
set /p choice="Choose an option: "

if "%choice%"=="1" goto start_app
if "%choice%"=="2" goto regression
if "%choice%"=="3" goto naive
if "%choice%"=="4" goto static
if "%choice%"=="5" goto reports
if "%choice%"=="6" goto open_reports
if "%choice%"=="7" goto down
if "%choice%"=="0" goto end
echo Not a valid option.
goto menu

:start_app
echo.
echo Starting SecureShop via Docker (this can take a minute or two)...
echo If port 5432 is already in use on your machine, set POSTGRES_PORT first, e.g.:
echo     set POSTGRES_PORT=5433
docker compose -f docker-compose.yml -f red_team\docker-compose.override.yml up -d --build --wait
if errorlevel 1 (
    echo.
    echo Docker reported an error above. Read it before retrying — do not assume it worked.
) else (
    echo.
    echo Containers should be up. Check with: docker compose ps
    echo Then open https://localhost/ in a browser and accept the local self-signed certificate once.
)
pause
goto menu

:regression
echo.
echo Running the live regression tests against https://localhost ...
echo This only works if step 1 has been run first and the app is reachable.
python red_team\live_tests\run_regression.py
echo.
echo Results written to red_team\evidence\live\regression_results.md
pause
goto menu

:naive
echo.
echo Starting the Naive Shop (pure Python, no Docker) in a new window...
start "Naive Shop (insecure demo)" cmd /k python naive_shop\app.py
echo Waiting a moment for it to start...
timeout /t 2 >nul
echo Running attacks against it...
python red_team\live_tests\attack_naive.py
echo.
echo Results written to red_team\evidence\naive_shop\attack_results.md
echo Close the "Naive Shop" window when you're done — it must not be left running.
pause
goto menu

:static
echo.
echo Running Bandit (Python static analysis)...
bandit -r . -x "./.venv,./.git,./red_team,./naive_shop,./certs,./docs" -f json -o red_team\reports\bandit_results.json
echo.
echo Running pip-audit (dependency vulnerability scan)...
pip-audit -r requirements.txt --format json -o red_team\reports\pip_audit.json
echo.
echo Done. Review red_team\reports\bandit_results.json and pip_audit.json,
echo and re-check any new finding by hand before trusting it.
pause
goto menu

:reports
echo.
echo Rebuilding HTML reports from the markdown sources...
python red_team\reports\build_reports.py
echo.
echo HTML done. For PDFs, open each report and use the browser's
echo "Print to PDF", or run the WeasyPrint export described in RUN_GUIDE.md section 5.
pause
goto menu

:open_reports
start "" "red_team\reports\index.html"
goto menu

:down
echo.
echo Stopping SecureShop containers (data is kept)...
docker compose down
pause
goto menu

:end
endlocal
exit /b 0
