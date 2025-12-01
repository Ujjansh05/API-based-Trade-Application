@echo off
echo ========================================
echo Antigravity Trader - Complete Build
echo ========================================
echo.

REM Step 1: Build Backend
echo [1/3] Building Backend Executable...
cd backend
python -m PyInstaller --onefile --name "AntigravityBackend" --add-data ".env;." backend_runner.py
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
call npm run electron:build
if errorlevel 1 (
    echo ERROR: Electron packaging failed!
    pause
    exit /b 1
)
cd ..
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
