@echo off
setlocal EnableExtensions
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
pushd "%ROOT%" || exit /b 1

set "PY=%ROOT%\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
set "LOGDIR=%ROOT%\red_team\evidence\runner"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmssfff"') do set "STAMP=%%T"
set "LOG=%LOGDIR%\run_%STAMP%_%RANDOM%.log"
echo CET431 Red Team runner started %DATE% %TIME%>"%LOG%"

:MENU
echo.
echo ============================================================
echo CET431 Red Team - local authorized test runner
echo Log: %LOG%
echo ============================================================
echo 1. Start SecureShop (Docker; migrations may run after consent)
echo 2. Run SecureShop live regression tests (explicit authorization)
echo 3. Start Naive Shop and run V1-V7
echo 4. Run Bandit and pip-audit
echo 5. Run all safe tests (in-memory + loopback Naive Shop)
echo 6. Generate final PDF
echo 7. Open final PDF
echo 8. Stop SecureShop containers
echo 9. Exit
set "CHOICE="
set /p "CHOICE=Select an option: "
if not defined CHOICE goto EXIT_RUNNER
if "%CHOICE%"=="1" goto START_SECURE
if "%CHOICE%"=="2" goto LIVE_TESTS
if "%CHOICE%"=="3" goto NAIVE_TESTS
if "%CHOICE%"=="4" goto STATIC_TESTS
if "%CHOICE%"=="5" goto SAFE_TESTS
if "%CHOICE%"=="6" goto MAKE_PDF
if "%CHOICE%"=="7" goto OPEN_PDF
if "%CHOICE%"=="8" goto STOP_SECURE
if "%CHOICE%"=="9" goto EXIT_RUNNER
echo Invalid choice.
goto MENU

:START_SECURE
echo Startup runs migrations and may seed demo data.
echo It uses a new timestamped Compose project and isolated PostgreSQL volume.
set "CONFIRM="
set /p "CONFIRM=Type I AUTHORIZE DISPOSABLE START AND MIGRATIONS to continue: "
if not "%CONFIRM%"=="I AUTHORIZE DISPOSABLE START AND MIGRATIONS" (
  echo NOT TESTED: startup was not authorized.
  echo [NOT TESTED] SecureShop startup not authorized.>>"%LOG%"
  goto MENU
)
where.exe docker >nul 2>&1
if errorlevel 1 (
  echo NOT TESTED: Docker CLI is unavailable.
  echo [NOT TESTED] Docker CLI unavailable.>>"%LOG%"
  goto MENU
)
if defined COMPOSE_PROJECT_NAME (
  echo INCONCLUSIVE: stop the current runner-created project before starting another.
  echo [INCONCLUSIVE] Disposable Compose project already active: %COMPOSE_PROJECT_NAME%.>>"%LOG%"
  goto MENU
)
set "COMPOSE_PROJECT_NAME=cet431-redteam-%STAMP%"
call :RUN_COMPOSE -p "%COMPOSE_PROJECT_NAME%" up -d --no-build --pull never web nginx
if not "%RC%"=="0" set "COMPOSE_PROJECT_NAME="
goto MENU

:LIVE_TESTS
echo Live regression writes authentication and audit state.
echo Never point it at the shared PostgreSQL database or real accounts.
if /I not "%SECURESHOP_TEST_ENVIRONMENT%"=="disposable" (
  echo NOT TESTED: SECURESHOP_TEST_ENVIRONMENT must be disposable.
  echo [NOT TESTED] No disposable SecureShop clone configured.>>"%LOG%"
  goto MENU
)
if not defined SECURESHOP_TEST_CUSTOMER_USER goto MISSING_LIVE_CREDS
if not defined SECURESHOP_TEST_CUSTOMER_PASSWORD goto MISSING_LIVE_CREDS
if not defined SECURESHOP_TEST_STAFF_USER goto MISSING_LIVE_CREDS
if not defined SECURESHOP_TEST_STAFF_PASSWORD goto MISSING_LIVE_CREDS
if not defined SECURESHOP_TEST_ADMIN_USER goto MISSING_LIVE_CREDS
if not defined SECURESHOP_TEST_ADMIN_PASSWORD goto MISSING_LIVE_CREDS
set "CONFIRM="
set /p "CONFIRM=Type I AUTHORIZE TESTS ON DISPOSABLE LOCAL CLONE to continue: "
if not "%CONFIRM%"=="I AUTHORIZE TESTS ON DISPOSABLE LOCAL CLONE" (
  echo NOT TESTED: live tests were not authorized.
  echo [NOT TESTED] Live SecureShop regression not authorized.>>"%LOG%"
  goto MENU
)
set "HTTP_CODE="
for /f %%S in ('curl.exe -k -s -o NUL -w "%%{http_code}" --connect-timeout 2 https://localhost/') do set "HTTP_CODE=%%S"
if "%HTTP_CODE%"=="000" (
  echo NOT TESTED: https://localhost is not reachable.
  echo [NOT TESTED] SecureShop HTTPS target unavailable.>>"%LOG%"
  goto MENU
)
set "SECURESHOP_LIVE_TESTS_AUTHORIZED=I AUTHORIZE TESTS ON DISPOSABLE LOCAL CLONE"
set "SECURESHOP_URL=https://localhost"
call :RUN_PY red_team\live_tests\run_regression.py
set "SECURESHOP_LIVE_TESTS_AUTHORIZED="
goto MENU

:MISSING_LIVE_CREDS
echo NOT TESTED: configure disposable customer, staff, and admin credentials in the environment.
echo [NOT TESTED] Disposable role credentials missing.>>"%LOG%"
goto MENU

:NAIVE_TESTS
call :RUN_PY red_team\live_tests\run_naive_suite.py
goto MENU

:STATIC_TESTS
call :RUN_PY red_team\live_tests\run_static_analysis.py
goto MENU

:SAFE_TESTS
call :RUN_PY red_team\live_tests\run_safe_tests.py
goto MENU

:MAKE_PDF
if not exist "%ROOT%\red_team\reports\FINAL_SECURITY_ASSESSMENT_REPORT.pdf" goto MAKE_PDF_FIRST
set "CONFIRM="
set /p "CONFIRM=Final PDF exists. Type REGENERATE FINAL PDF to replace our generated report: "
if not "%CONFIRM%"=="REGENERATE FINAL PDF" (
  echo NOT TESTED: PDF generation cancelled; existing report preserved.
  echo [NOT TESTED] PDF regeneration cancelled.>>"%LOG%"
  goto MENU
)
call :RUN_PY red_team\live_tests\generate_final_report.py --replace-existing
goto MENU

:MAKE_PDF_FIRST
call :RUN_PY red_team\live_tests\generate_final_report.py
goto MENU

:OPEN_PDF
set "PDF=%ROOT%\red_team\reports\FINAL_SECURITY_ASSESSMENT_REPORT.pdf"
if not exist "%PDF%" (
  echo NOT TESTED: final PDF does not exist yet. Select option 6 first.
  echo [NOT TESTED] Final PDF not found.>>"%LOG%"
  goto MENU
)
powershell -NoProfile -Command "Start-Process -FilePath '%PDF%'"
if errorlevel 1 (
  echo FAIL: could not open the final PDF.
  echo [FAIL] Could not open final PDF.>>"%LOG%"
) else (
  echo PASS: opened the final PDF with the system PDF handler.
  echo [PASS] Opened final PDF.>>"%LOG%"
)
goto MENU

:STOP_SECURE
if not defined COMPOSE_PROJECT_NAME (
  echo NOT TESTED: this runner has not started an isolated SecureShop Compose project.
  echo [NOT TESTED] No runner-owned Compose project is active.>>"%LOG%"
  goto MENU
)
set "CONFIRM="
set /p "CONFIRM=Type STOP LOCAL SECURESHOP to stop the project containers: "
if not "%CONFIRM%"=="STOP LOCAL SECURESHOP" (
  echo NOT TESTED: stop was not confirmed.
  echo [NOT TESTED] SecureShop stop not confirmed.>>"%LOG%"
  goto MENU
)
where.exe docker >nul 2>&1
if errorlevel 1 (
  echo NOT TESTED: Docker CLI is unavailable.
  echo [NOT TESTED] Docker CLI unavailable for stop.>>"%LOG%"
  goto MENU
)
call :RUN_COMPOSE -p "%COMPOSE_PROJECT_NAME%" stop
if "%RC%"=="0" set "COMPOSE_PROJECT_NAME="
goto MENU

:RUN_PY
set "SCRIPT=%ROOT%\%~1"
set "ARGS=%~2"
echo [COMMAND] "%PY%" "%SCRIPT%" %ARGS%>>"%LOG%"
set "TEMPLOG=%TEMP%\cet431-%STAMP%-%RANDOM%.tmp"
"%PY%" "%SCRIPT%" %ARGS% > "%TEMPLOG%" 2>&1
set "RC=%ERRORLEVEL%"
if exist "%TEMPLOG%" (
  type "%TEMPLOG%"
  type "%TEMPLOG%">>"%LOG%"
  del "%TEMPLOG%"
)
if "%RC%"=="0" (
  echo [COMPLETED] %~nx1 exited successfully; see script-level results above.>>"%LOG%"
  echo COMPLETED: %~nx1 exited successfully; see script-level results above.
) else if "%RC%"=="2" (
  echo [INCONCLUSIVE] %~nx1 exit %RC%.>>"%LOG%"
  echo INCONCLUSIVE: %~nx1 exit %RC%.
) else (
  echo [FAIL] %~nx1 exit %RC%.>>"%LOG%"
  echo FAIL: %~nx1 exit %RC%.
)
exit /b

:RUN_COMPOSE
echo [COMMAND] docker compose %*>>"%LOG%"
set "TEMPLOG=%TEMP%\cet431-%STAMP%-%RANDOM%.tmp"
docker compose %* > "%TEMPLOG%" 2>&1
set "RC=%ERRORLEVEL%"
if exist "%TEMPLOG%" (
  type "%TEMPLOG%"
  type "%TEMPLOG%">>"%LOG%"
  del "%TEMPLOG%"
)
if "%RC%"=="0" (
  echo [COMPLETED] docker compose %*>>"%LOG%"
  echo COMPLETED: docker compose %*
) else (
  echo [FAIL] docker compose %* (exit %RC%)>>"%LOG%"
  echo FAIL: docker compose %* (exit %RC%)
)
exit /b

:EXIT_RUNNER
echo [INFO] Runner exited %DATE% %TIME%.>>"%LOG%"
popd
echo Run log: %LOG%
exit /b 0
