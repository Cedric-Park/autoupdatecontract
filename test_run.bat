@echo off
chcp 65001 >nul
echo 🧪 게임더하기 크롤링 직접 테스트
echo.

cd /d "%~dp0"

echo 📍 현재 디렉토리: %CD%
echo 📍 Python 버전:
python --version
echo.

echo 🚀 크롤링을 시작합니다...
echo ⚠️  이 창을 닫지 마세요. 크롤링이 진행 중입니다...
echo.

python login_and_crawl.py

echo.
echo ✅ 크롤링이 완료되었습니다.
echo 📝 결과를 확인하고 창을 닫으세요.
pause 