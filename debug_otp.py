"""
OTP 인증 모달의 HTML 요소를 디버깅하기 위한 스크립트
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()
USER_ID = os.environ.get('USER_ID')
USER_PW = os.environ.get('USER_PW')

# 로그인 URL
LOGIN_URL = 'https://gsp.kocca.kr/admin'

def debug_otp_modal():
    # 크롬 드라이버 설정 - 헤드리스 모드 사용하지 않음 (시각적으로 확인하기 위함)
    options = Options()
    options.add_argument('--start-maximized')  # 브라우저 창 최대화
    
    try:
        # 드라이버 로드
        chrome_driver_path = "./chromedriver.exe"
        driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
        print("크롬 드라이버 로드 성공!")
    except Exception as e:
        print(f"드라이버 로드 실패: {e}")
        return
    
    try:
        # 로그인 페이지 접속
        print("로그인 페이지로 이동 중...")
        driver.get(LOGIN_URL)
        time.sleep(3)
        
        # 로그인 폼 찾기
        id_input = driver.find_element(By.ID, 'j_username')
        pw_input = driver.find_element(By.ID, 'j_password')
        
        # 로그인 시도
        print("로그인 시도 중...")
        id_input.send_keys(USER_ID)
        pw_input.send_keys(USER_PW)
        pw_input.send_keys('\n')  # Enter 키 입력
        time.sleep(3)
        
        # OTP 모달 디버깅
        print("OTP 모달 디버깅 시작...")
        print(f"현재 URL: {driver.current_url}")
        
        # 페이지의 모든 모달 찾기
        modals = driver.find_elements(By.CSS_SELECTOR, '.modal, [role="dialog"], [class*="modal"], [id*="modal"], [class*="otp"], [id*="otp"]')
        print(f"발견된 모달/다이얼로그 요소: {len(modals)}개")
        
        # 모달 정보 출력
        for i, modal in enumerate(modals):
            print(f"\n모달 #{i+1}:")
            print(f"  ID: {modal.get_attribute('id')}")
            print(f"  Class: {modal.get_attribute('class')}")
            print(f"  Role: {modal.get_attribute('role')}")
            print(f"  Visible: {modal.is_displayed()}")
            
            # 모달 내부의 입력 필드 찾기
            inputs = modal.find_elements(By.CSS_SELECTOR, 'input')
            print(f"  입력 필드: {len(inputs)}개")
            for j, input_field in enumerate(inputs):
                print(f"    입력 필드 #{j+1}:")
                print(f"      ID: {input_field.get_attribute('id')}")
                print(f"      Type: {input_field.get_attribute('type')}")
                print(f"      Name: {input_field.get_attribute('name')}")
                
            # 모달 내부의 버튼 찾기
            buttons = modal.find_elements(By.CSS_SELECTOR, 'button, input[type="submit"], input[type="button"]')
            print(f"  버튼: {len(buttons)}개")
            for j, button in enumerate(buttons):
                print(f"    버튼 #{j+1}:")
                print(f"      ID: {button.get_attribute('id')}")
                print(f"      Text: {button.text}")
                print(f"      Type: {button.get_attribute('type')}")
        
        # 페이지 소스 저장
        with open("otp_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\n페이지 소스를 'otp_page_source.html'에 저장했습니다.")
        
        # 스크린샷 저장
        driver.save_screenshot("otp_modal.png")
        print("스크린샷을 'otp_modal.png'에 저장했습니다.")
        
        # 사용자 입력 대기 (수동으로 확인할 시간)
        input("OTP 모달을 확인한 후 Enter 키를 눌러 계속하세요...")
        
    except Exception as e:
        print(f"디버깅 중 오류 발생: {e}")
    finally:
        driver.quit()
        print("브라우저 종료됨")

if __name__ == "__main__":
    debug_otp_modal()