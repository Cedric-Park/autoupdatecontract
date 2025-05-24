@echo off
chcp 65001 >nul
echo 🎮 게임더하기 계약 관리 자동화 대시보드를 시작합니다...
echo.

cd /d "%~dp0"

python dashboard.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 대시보드 실행 중 오류가 발생했습니다.
    echo 오류 코드: %ERRORLEVEL%
    echo.
    echo Python이 설치되어 있는지 확인해주세요.
    pause
) else (
    echo.
    echo ✅ 대시보드가 정상적으로 종료되었습니다.
) 