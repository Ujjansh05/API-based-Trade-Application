@echo off
echo ========================================
echo Antigravity Trader - Complete Build
echo ========================================
echo.

REM Step 0: Configure mStock Credentials (.env)
echo [0/3] Configure mStock credentials for live feed
setlocal enabledelayedexpansion
set "ENV_FILE=.env"
echo.
echo Enter your mStock API Key, User ID and Password.
echo These will be saved to %ENV_FILE% in this folder.
echo.
set /p MSTOCK_API_KEY=API Key: 
set /p MSTOCK_USER_ID=User ID: 
set /p MSTOCK_PASSWORD=Password: 

echo Creating/Updating %ENV_FILE% ...
> "%ENV_FILE%" echo MSTOCK_API_KEY=!MSTOCK_API_KEY!
>> "%ENV_FILE%" echo MSTOCK_USER_ID=!MSTOCK_USER_ID!
>> "%ENV_FILE%" echo MSTOCK_PASSWORD=!MSTOCK_PASSWORD!
echo Saved credentials to %ENV_FILE%
echo.
endlocal

REM Step 1: Build Backend
echo [1/3] Building Backend Executable...
cd backend
python -m PyInstaller --onefile --name "AntigravityBackend" backend_runner.py
if errorlevel 1 (
    echo ERROR: Backend build failed!
    pause
    exit /b 1
)
cd ..
echo Backend build complete!
echo.

REM Step 2: Build Frontend  
echo [2/3] Building Frontend...
cd frontend
echo Cleaning previous build artifacts...
echo Attempting to terminate any running Electron app instances...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Process | Where-Object { $_.ProcessName -like '*Antigravity*' -or $_.ProcessName -like '*electron*' } | Stop-Process -Force -ErrorAction SilentlyContinue"
timeout /t 2 >nul
if exist dist (
    rmdir /S /Q dist
)
if exist dist-electron (
    rmdir /S /Q dist-electron
)
echo Installing dependencies (npm ci)...
call npm ci
echo Building Vite app...
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    pause
    exit /b 1
)
echo Frontend build complete!
echo.

REM Step 3: Package Electron App
echo [3/3] Packaging Electron Application...
set NODE_ENV=production
call npm run electron:build
if errorlevel 1 (
    echo ERROR: Electron packaging failed!
    pause
    exit /b 1
)
cd ..
echo.

REM Smoke Check: Start backend and verify live mode
echo Running backend smoke-check (verifying live status)...
set "SMOKE_PORT=8000"
for /f "tokens=*" %%i in ('powershell -NoProfile -Command "$pid"') do set "PWSH_PID=%%i"
start "AntigravityBackendServer" powershell -NoProfile -Command "Push-Location '%cd%\backend'; $env:MSTOCK_API_KEY=(Get-Content '..\.env' | Select-String '^MSTOCK_API_KEY=' | ForEach-Object { $_.ToString().Split('=')[1] }); $env:MSTOCK_USER_ID=(Get-Content '..\.env' | Select-String '^MSTOCK_USER_ID=' | ForEach-Object { $_.ToString().Split('=')[1] }); $env:MSTOCK_PASSWORD=(Get-Content '..\.env' | Select-String '^MSTOCK_PASSWORD=' | ForEach-Object { $_.ToString().Split('=')[1] }); python -m uvicorn main:app --port %SMOKE_PORT%" 
timeout /t 5 >nul
curl -s http://127.0.0.1:%SMOKE_PORT% > smoke_status.json
echo Backend status:
type smoke_status.json
echo.
echo Sample live LTPs (first 5):
powershell -NoProfile -Command "try { $t = Invoke-RestMethod -Uri 'http://127.0.0.1:%SMOKE_PORT%/api/tokens' -Method GET; $t | Select-Object -First 5 | ForEach-Object { '{0}`t{1}' -f $_.symbol, $_.ltp } | Out-File -FilePath 'tokens_sample.txt' -Encoding utf8 } catch { 'Error fetching tokens' | Out-File -FilePath 'tokens_sample.txt' -Encoding utf8 }"
type tokens_sample.txt
echo.
echo Stopping backend server...
for /f "tokens=2 delims==" %%p in ('wmic process where "CommandLine like '%%uvicorn%%'" get ProcessId /value ^| find "ProcessId="') do taskkill /F /PID %%p >nul 2>&1
del smoke_status.json >nul 2>&1
del tokens_sample.txt >nul 2>&1
echo Smoke-check complete.
echo.

echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo Installer created at:
echo frontend\dist\Antigravity Trader Setup.exe
echo.
echo You can now distribute this file to clients.
echo.
pause
