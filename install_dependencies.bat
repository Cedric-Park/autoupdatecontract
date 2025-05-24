@echo off
chcp 65001 >nul
echo 🔧 게임더하기 계약 관리 자동화 시스템 패키지 설치를 시작합니다...
echo.

cd /d "%~dp0"

echo 📦 Python 버전 확인...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo Python 3.8 이상을 설치해주세요.
    pause
    exit /b 1
)

echo.
echo 📦 pip 업그레이드 중...
python -m pip install --upgrade pip

echo.
echo 📦 필수 패키지 설치 중...
pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 모든 패키지가 성공적으로 설치되었습니다!
    echo.
    echo 🚀 이제 다음 파일들을 실행할 수 있습니다:
    echo   - start_dashboard.bat : GUI 대시보드 실행
    echo   - run_automation.bat  : 자동화 프로그램 1회 실행
    echo.
) else (
    echo.
    echo ❌ 패키지 설치 중 오류가 발생했습니다.
    echo 인터넷 연결을 확인하고 다시 시도해주세요.
)

pause 