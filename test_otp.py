"""
OTP 코드 생성 테스트 스크립트
"""
import os
import pyotp
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()
OTP_SECRET = os.environ.get('OTP_SECRET')

def test_otp_generation():
    """
    OTP 비밀 키를 사용하여 OTP 코드 생성 테스트
    """
    if not OTP_SECRET:
        print("[ERROR] OTP 비밀 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
        
    try:
        # TOTP 객체 생성
        totp = pyotp.TOTP(OTP_SECRET)
        
        # 현재 시간에 유효한 OTP 코드 생성
        otp_code = totp.now()
        print(f"생성된 OTP 코드: {otp_code}")
        print(f"이 코드는 약 30초 동안 유효합니다.")
        
        # 코드 유효성 확인
        is_valid = totp.verify(otp_code)
        print(f"코드 유효성 확인: {'유효함' if is_valid else '유효하지 않음'}")
        
        # 남은 시간 계산
        import time
        remaining = 30 - (int(time.time()) % 30)
        print(f"다음 코드까지 남은 시간: {remaining}초")
        
    except Exception as e:
        print(f"[ERROR] OTP 코드 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    test_otp_generation()