from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv

# 로그인 정보
LOGIN_URL = 'https://gsp.kocca.kr/admin'
SERVICE_REQ_URL = 'https://gsp.kocca.kr/admin/serviceReq/serviceReqListPage.do'
USER_ID = None  # 환경 변수에서 가져옴
USER_PW = None  # 환경 변수에서 가져옴

# 크롬 드라이버 설정
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 브라우저 창을 띄우지 않음
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

# .env 파일에서 환경변수 불러오기
def load_env():
    load_dotenv()
    global USER_ID, USER_PW, EMAIL_SENDER, EMAIL_APP_PASSWORD
    USER_ID = os.environ.get('USER_ID', 'com2us30')  # 기본값 제공
    USER_PW = os.environ.get('USER_PW', 'com2us!@#$')  # 기본값 제공
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
    EMAIL_APP_PASSWORD = os.environ.get('EMAIL_APP_PASSWORD')

def login():
    # 환경 변수 로드 확인
    if USER_ID is None or USER_PW is None:
        load_env()
        print(f"로그인 정보 로드: ID={USER_ID}")
        
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"기본 드라이버 로드 실패: {e}")
        try:
            # 백업 방법: 직접 경로 지정
            chrome_driver_path = "./chromedriver.exe"  # 크롬 드라이버를 프로젝트 폴더에 넣은 경우
            driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
        except Exception as e:
            print(f"직접 지정 드라이버 로드 실패: {e}")
            return None
    
    print("브라우저 시작 - 로그인 페이지로 이동 중...")
    driver.get(LOGIN_URL)
    time.sleep(3)  # 페이지 로딩 대기 시간 증가
    
    print(f"현재 URL: {driver.current_url}")
    
    # 로그인 폼이 실제로 존재하는지 체크
    try:
        # 로그인 폼 찾기 시도
        id_input = driver.find_element(By.ID, 'j_username')
        pw_input = driver.find_element(By.ID, 'j_password')
        
        # 로그인 폼이 있으면 로그인 시도
        print("로그인 폼 발견 - 로그인 시도 중...")
        id_input.send_keys(USER_ID)
        pw_input.send_keys(USER_PW)
        pw_input.send_keys(Keys.RETURN)
        time.sleep(3)  # 로그인 처리 대기 시간 증가
    except Exception as e:
        print(f'로그인 폼 찾기 실패: {e}')
        # 이미 로그인되어 있는지 확인
        if 'admin' in driver.current_url and 'login' not in driver.current_url:
            print('이미 로그인된 상태로 확인됨')
        else:
            print('로그인 폼이 없지만 로그인 상태도 아님')
            driver.save_screenshot('login_error.png')  # 디버깅용 스크린샷
            driver.quit()
            return None
    
    # 로그인 성공 여부를 관리자 페이지 URL로 명확히 확인
    print(f"로그인 후 URL: {driver.current_url}")
    if 'admin' in driver.current_url and 'login' not in driver.current_url:
        print('로그인 성공!')
        return driver
    else:
        print('로그인 실패 또는 세션 만료!')
        driver.save_screenshot('login_failed.png')  # 디버깅용 스크린샷
        driver.quit()
        return None

def get_estimate_status(driver, estimate_link):
    """
    견적서 제출 건 링크 클릭 → 상세페이지 진입 → 협력사/금액/일자 모두 추출 후 문자열 반환
    """
    estimate_link.click()
    # 상세페이지 테이블 로딩 대기
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.division30 #dataList"))
    )
    time.sleep(1)  # 페이지 렌더링 여유
    detail_rows = driver.find_elements(By.CSS_SELECTOR, "div.division30 #dataList tbody tr")
    estimates = []
    for drow in detail_rows:
        dtds = drow.find_elements(By.TAG_NAME, "td")
        if len(dtds) < 7:
            continue
        협력사 = dtds[2].text.strip()
        견적일자 = dtds[4].text.strip()
        견적금액 = dtds[5].text.strip()
        estimates.append(f"{협력사}({견적금액}, {견적일자})")
    # 원래 페이지로 복귀
    driver.back()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "dataList"))
    )
    time.sleep(1)
    return '\n'.join(estimates) if estimates else "없음"

def crawl_service_req_table_with_estimate(driver):
    # 첫 페이지 로드
    driver.get(SERVICE_REQ_URL)
    
    # 로그인 여부 재확인
    if 'admin' not in driver.current_url or 'login' in driver.current_url:
        print("세션이 종료되었거나 로그인 상태가 아닙니다. 다시 로그인합니다.")
        driver = login()
        if not driver:
            return []
        driver.get(SERVICE_REQ_URL)
    
    all_data = []
    MAX_PAGES = 5  # 최대 5페이지까지만 크롤링
    
    # 기본 URL 가져오기
    base_url = driver.current_url
    print(f"기본 URL: {base_url}")
    
    for current_page in range(1, MAX_PAGES + 1):
        print(f"현재 페이지 {current_page} 크롤링 중...")
        
        if current_page > 1:
            # URL을 직접 구성하여 다른 페이지로 이동
            # 기본형: https://gsp.kocca.kr/admin/serviceReq/serviceReqListPage.do
            # 페이지 파라미터 추가: ?pageIndex=2
            page_url = f"{base_url}?pageIndex={current_page}"
            print(f"페이지 URL: {page_url}")
            driver.get(page_url)
            time.sleep(3)  # 페이지 로딩 대기
        
        try:
            # 테이블 찾기
            table = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "dataList"))
            )
            
            # 현재 페이지의 테이블 데이터 추출
            rows = table.find_elements(By.TAG_NAME, 'tr')
            data = []
            
            if len(rows) <= 1:  # 헤더만 있고 데이터가 없는 경우
                print(f"페이지 {current_page}에 데이터가 없습니다. 크롤링 종료.")
                break
                
            for i, row in enumerate(rows):
                try:
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    if not cols or len(cols) < 8:
                        continue
                    row_data = [col.text.strip() for col in cols]
                    
                    # 견적서 제출 건이 1건 이상이면 상세페이지 진입
                    try:
                        estimate_text = cols[5].text.strip()
                        estimate_link = cols[5].find_element(By.TAG_NAME, "a")
                        if estimate_text and estimate_text != "0건":
                            estimate_status = get_estimate_status(driver, estimate_link)
                        else:
                            estimate_status = "없음"
                    except Exception as e:
                        print(f"견적서 상세 정보 가져오기 실패: {e}")
                        estimate_status = "없음"
                        
                    row_data.append(estimate_status)  # 견적서제출현황 컬럼 추가
                    data.append(row_data)
                except Exception as e:
                    print(f"행 데이터 추출 중 오류: {e}")
                    continue
            
            print(f"페이지 {current_page}에서 {len(data)}개 항목 추출 완료")
            all_data.extend(data)
            
        except Exception as e:
            print(f"페이지 {current_page} 크롤링 중 오류: {e}")
            break
    
    return all_data

def filter_2025_deadline(data):
    """
    입찰 마감일이 2025년인 항목만 필터링하는 함수
    """
    filtered = []
    for row in data:
        if len(row) < 7:
            continue
        deadline = row[6]  # 7번째 컬럼: 입찰 마감일
        if deadline and deadline.startswith('2025'):
            filtered.append(row)
    return filtered 