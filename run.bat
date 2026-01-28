@echo off
echo SecureBank 온라인 뱅킹 시스템 시작 중...
echo.

REM 가상환경이 있는지 확인
if not exist "venv" (
    echo 가상환경을 생성합니다...
    python -m venv venv
)

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM 의존성 설치
echo 필요한 패키지를 설치합니다...
pip install -r requirements.txt

REM 애플리케이션 실행
echo.
echo SecureBank 웹 서버를 시작합니다...
echo 브라우저에서 http://localhost:5000 으로 접속하세요.
echo.
python app.py

pause