"""
OTP 인증이 포함된 로그인 테스트 스크립트
"""
from browser_utils import login
import time

def main():
    print("[TEST] OTP 인증이 포함된 로그인 테스트 시작")
    
    # 로그인 시도 (OTP 인증 포함)
    driver = login()
    
    if driver:
        print("[SUCCESS] 로그인 성공! (OTP 인증 완료)")
        
        # 로그인 상태 확인
        current_url = driver.current_url
        print(f"현재 URL: {current_url}")
        
        # 스크린샷 저장 (성공 확인용)
        driver.save_screenshot("login_success.png")
        print("스크린샷을 'login_success.png'에 저장했습니다.")
        
        # 잠시 대기 후 브라우저 종료
        time.sleep(3)
        driver.quit()
    else:
        print("[FAILED] 로그인 실패 (OTP 인증 포함)")

if __name__ == "__main__":
    main()