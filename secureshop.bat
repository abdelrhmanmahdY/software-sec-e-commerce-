@echo off
REM ============================================================
REM  SecureShop - single control panel (Red Team + app runner)
REM  Double-click, then pick a number.
REM ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title SecureShop Control Panel

REM --- pick a python: venv if present, else system ---
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

:menu
cls
echo ============================================================
echo                 SecureShop Control Panel
echo ============================================================
echo   APP
echo    1) Start app with Docker   (build + seed + open browser)
echo    2) Start app with local venv
echo    3) Stop the Docker app
echo.
echo   RED TEAM
echo    4) Run lab demos           (Labs 1-5, educational)
echo    5) Run live baseline tests (needs the app running)
echo    6) Open reports
echo.
echo    7) FULL PRESENTATION       (Docker + demos + live tests + report)
echo    0) Exit
echo ============================================================
set /p "choice=Choose a number: "

if "%choice%"=="1" goto docker_start
if "%choice%"=="2" goto venv_start
if "%choice%"=="3" goto docker_stop
if "%choice%"=="4" goto demos
if "%choice%"=="5" goto live
if "%choice%"=="6" goto reports
if "%choice%"=="7" goto present
if "%choice%"=="0" goto end
goto menu

:ensure_env
if not exist ".env" if exist ".env.example" copy /y ".env.example" ".env" >nul
exit /b 0

:docker_start
call :ensure_env
docker info >nul 2>&1
if errorlevel 1 ( echo [ERROR] Docker is not running. Open Docker Desktop first. & pause & goto menu )
echo [*] Building and starting containers (first run is slow)...
docker compose up --build -d
if errorlevel 1 ( echo [ERROR] docker compose failed. & pause & goto menu )
echo [*] Waiting, then seeding test data...
timeout /t 8 >nul
docker compose exec -T web python manage.py seed_data
start http://localhost:8000/
echo [*] App running at http://localhost:8000/
pause
goto menu

:docker_stop
docker compose down
echo [*] Stopped. (Database kept in the postgres_data volume.)
pause
goto menu

:venv_start
call :ensure_env
if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating virtual environment...
    python -m venv .venv || ( echo [ERROR] venv failed. Install Python 3.11+. & pause & goto menu )
    set "PY=.venv\Scripts\python.exe"
    echo [*] Installing dependencies (one time, please wait)...
    "!PY!" -m pip install --upgrade pip
    "!PY!" -m pip install -r requirements.txt || ( echo [ERROR] install failed. & pause & goto menu )
)
set "PY=.venv\Scripts\python.exe"
echo [*] Applying migrations and seeding...
"%PY%" manage.py migrate
"%PY%" manage.py seed_data
start http://127.0.0.1:8000/
start "SecureShop server" cmd /k ""%PY%" manage.py runserver 127.0.0.1:8000"
echo [*] Server started in a new window. Close that window to stop it.
pause
goto menu

:demos
echo ============================================================
echo  Lab demos (educational examples - naive vs secure)
echo ============================================================
for %%F in (
  "red_team\labs\lab1_client_side_trust\naive_price_demo.py"
  "red_team\labs\lab2_business_logic\coupon_replay_demo.py"
  "red_team\labs\lab2_business_logic\email_truncation_demo.py"
  "red_team\labs\lab2_business_logic\workflow_skip_demo.py"
  "red_team\labs\lab3_authentication\auth_identity_demo.py"
  "red_team\labs\lab4_anomaly_detection\anomaly_detection_demo.py"
  "red_team\labs\lab5_location_time_passkey\defense_checks_demo.py"
) do (
  echo.
  echo ----- %%~nxF -----
  "%PY%" %%F
)
echo.
pause
goto menu

:live
echo ============================================================
echo  Live baseline tests against http://127.0.0.1:8000
echo ============================================================
"%PY%" red_team\live_tests\run_live_tests.py
echo.
pause
goto menu

:reports
start "" "red_team\reports\live_baseline_report.md"
start "" "red_team\reports\coverage_matrix.md"
start "" "red_team\reports\pentest_report_template.md"
echo [*] Opened the reports.
pause
goto menu

:present
call :ensure_env
docker info >nul 2>&1
if errorlevel 1 ( echo [ERROR] Docker is not running. Open Docker Desktop first. & pause & goto menu )
echo [1/4] Starting app with Docker...
docker compose up --build -d || ( echo [ERROR] docker failed. & pause & goto menu )
timeout /t 8 >nul
docker compose exec -T web python manage.py seed_data
start http://localhost:8000/
echo.
echo [2/4] Running lab demos...
call :demos_run
echo.
echo [3/4] Running live baseline tests...
"%PY%" red_team\live_tests\run_live_tests.py
echo.
echo [4/4] Opening the baseline report...
start "" "red_team\reports\live_baseline_report.md"
echo.
echo Presentation sequence done.
pause
goto menu

:demos_run
for %%F in (
  "red_team\labs\lab1_client_side_trust\naive_price_demo.py"
  "red_team\labs\lab2_business_logic\coupon_replay_demo.py"
  "red_team\labs\lab2_business_logic\email_truncation_demo.py"
  "red_team\labs\lab2_business_logic\workflow_skip_demo.py"
  "red_team\labs\lab3_authentication\auth_identity_demo.py"
  "red_team\labs\lab4_anomaly_detection\anomaly_detection_demo.py"
  "red_team\labs\lab5_location_time_passkey\defense_checks_demo.py"
) do (
  echo. & echo ----- %%~nxF ----- & "%PY%" %%F
)
exit /b 0

:end
endlocal
