@echo off
setlocal
echo ======================================================
echo    CRACK SERVER - PORTABLE LAUNCHER v1.2.8
echo ======================================================
echo.

:: 0. 압축 해제 여부 확인
if not exist "%~dp0app.py" (
    echo [ERROR] Please extract the ZIP file first.
    pause
    exit /b
)

:: 1. 파이썬 실행 파일 설정
set "PYTHON_EXE=python"
if exist "%~dp0python_portable\python.exe" (
    echo [*] Using local portable python...
    set "PYTHON_EXE=%~dp0python_portable\python.exe"
) else (
    echo [*] Checking system python...
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python not found. 
        echo Please read DEPLOY_HELP.txt for manual setup.
        pause
        exit /b
    )
)

:: 2. 기존 포트(8012) 종료
echo [*] Checking port 8012...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8012') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 3. 가상환경 체크 및 생성
if not exist "%~dp0.venv" (
    echo [*] Creating virtual environment...
    "%PYTHON_EXE%" -m venv "%~dp0.venv"
)

:: 4. 필수 라이브러리 설치
echo [*] Installing libraries (this may take a few minutes)...
call "%~dp0.venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>&1
pip install -r "%~dp0requirements.txt"

:: 5. 서버 실행
cls
echo ======================================================
echo    CRACK SERVER is running on http://localhost:8012
echo ======================================================
echo.
python "%~dp0app.py"

echo.
echo Server stopped.
pause
