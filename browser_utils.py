from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv
from selenium.webdriver.chrome.options import Options  # Options 클래스 명시적으로 임포트

# 로그인 정보
LOGIN_URL = 'https://gsp.kocca.kr/admin'
SERVICE_REQ_URL = 'https://gsp.kocca.kr/admin/serviceReq/serviceReqListPage.do'
USER_ID = None  # 환경 변수에서 가져옴
USER_PW = None  # 환경 변수에서 가져옴

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
        
    # 크롬 드라이버 설정
    options = Options()
    options.add_argument('--headless')  # 브라우저 창을 띄우지 않음
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    try:
        # 1. 먼저 프로젝트 폴더의 최신 드라이버 사용 시도
        chrome_driver_path = "./chromedriver.exe"  # 최신 드라이버 경로
        print(f"최신 크롬 드라이버 사용 시도: {chrome_driver_path}")
        driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
        print("최신 크롬 드라이버 로드 성공!")
    except Exception as e:
        print(f"최신 드라이버 로드 실패: {e}")
        try:
            # 2. 자동 감지 방식 시도
            print("자동 감지 방식으로 드라이버 로드 시도...")
            driver = webdriver.Chrome(options=options)
            print("자동 감지 드라이버 로드 성공!")
        except Exception as e:
            print(f"모든 드라이버 로드 방식 실패: {e}")
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
            # JavaScript 함수를 사용하여 페이지 이동
            print(f"JavaScript로 페이지 {current_page} 이동 중...")
            driver.execute_script(f"go_Page({current_page})")
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

def extract_estimate_number(estimate_cell):
    """
    견적서 제출 건 셀에서 serviceReqEstimateListPage('넘버') 추출
    """
    try:
        # <a href="javascript:serviceReqEstimateListPage('12345')">1건</a> 형태에서 넘버 추출
        link_element = estimate_cell.find_element(By.TAG_NAME, "a")
        href = link_element.get_attribute("href")
        
        # javascript:serviceReqEstimateListPage('12345') 에서 12345 추출
        import re
        match = re.search(r"serviceReqEstimateListPage\('(\d+)'\)", href)
        return match.group(1) if match else ""
    except:
        return ""

def crawl_all_pages_optimized(driver):
    """
    최적화된 크롤링: 1~15페이지 크롤링, 2025년 조건부 중단, 넘버 추출 포함
    """
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
    MAX_PAGES = 15  # 최대 15페이지까지 크롤링
    
    # 기본 URL 가져오기
    base_url = driver.current_url
    print(f"기본 URL: {base_url}")
    
    for current_page in range(1, MAX_PAGES + 1):
        print(f"현재 페이지 {current_page} 크롤링 중...")
        
        if current_page > 1:
            # JavaScript 함수를 사용하여 페이지 이동
            print(f"JavaScript로 페이지 {current_page} 이동 중...")
            driver.execute_script(f"go_Page({current_page})")
            time.sleep(3)  # 페이지 로딩 대기
        
        try:
            # 테이블 찾기
            table = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "dataList"))
            )
            
            # 현재 페이지의 테이블 데이터 추출
            rows = table.find_elements(By.TAG_NAME, 'tr')
            
            if len(rows) <= 1:  # 헤더만 있고 데이터가 없는 경우
                print(f"페이지 {current_page}에 데이터가 없습니다. 크롤링 종료.")
                break
            
            page_data = []
            stop_crawling = False
            
            for i, row in enumerate(rows):
                try:
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    if not cols or len(cols) < 8:
                        continue
                    
                    row_data = [col.text.strip() for col in cols]
                    
                    # 입찰 마감일 확인 (6번째 컬럼)
                    deadline = row_data[6] if len(row_data) > 6 else ""
                    if deadline and not deadline.startswith('2025'):
                        print(f"2025년이 아닌 입찰 마감일 발견: {deadline}. 크롤링 중단.")
                        stop_crawling = True
                        break
                    
                    # 견적서 제출 건 넘버 추출 (5번째 컬럼)
                    estimate_number = ""
                    try:
                        estimate_text = cols[5].text.strip()
                        if estimate_text and estimate_text != "0건":
                            estimate_number = extract_estimate_number(cols[5])
                    except Exception as e:
                        print(f"견적서 넘버 추출 실패: {e}")
                    
                    # 넘버를 별도 컬럼으로 추가 (10번째 위치)
                    row_data.append("")  # 9번째: 견적서제출현황 (나중에 필요시 업데이트)
                    row_data.append(estimate_number)  # 10번째: 견적서 넘버
                    
                    page_data.append(row_data)
                    
                except Exception as e:
                    print(f"행 데이터 추출 중 오류: {e}")
                    continue
            
            print(f"페이지 {current_page}에서 {len(page_data)}개 항목 추출 완료")
            all_data.extend(page_data)
            
            # 2025년 아닌 값 발견으로 중단
            if stop_crawling:
                break
                
        except Exception as e:
            print(f"페이지 {current_page} 크롤링 중 오류: {e}")
            break
    
    print(f"총 {len(all_data)}개 항목 크롤링 완료 (2025년 입찰 마감일 조건)")
    return all_data 

# 계약변경관리 페이지 URL 추가
CONTRACT_CHANGE_URL = 'https://gsp.kocca.kr/admin/contract/contractChangeListPage.do'

def crawl_contract_change_pages(driver):
    """
    계약변경관리 페이지 크롤링: 2025년 신청일 항목만 크롤링
    """
    # 첫 페이지 로드
    driver.get(CONTRACT_CHANGE_URL)
    
    # 로그인 여부 재확인
    if 'admin' not in driver.current_url or 'login' in driver.current_url:
        print("[CONTRACT_CHANGE] 세션이 종료되었거나 로그인 상태가 아닙니다. 다시 로그인합니다.")
        driver = login()
        if not driver:
            return []
        driver.get(CONTRACT_CHANGE_URL)
    
    all_data = []
    MAX_PAGES = 15  # 최대 15페이지까지 크롤링
    
    # 기본 URL 가져오기
    base_url = driver.current_url
    print(f"[CONTRACT_CHANGE] 기본 URL: {base_url}")
    
    for current_page in range(1, MAX_PAGES + 1):
        print(f"[CONTRACT_CHANGE] 현재 페이지 {current_page} 크롤링 중...")
        
        if current_page > 1:
            # JavaScript 함수를 사용하여 페이지 이동
            print(f"[CONTRACT_CHANGE] JavaScript로 페이지 {current_page} 이동 중...")
            driver.execute_script(f"go_Page({current_page})")
            time.sleep(5)  # 페이지 로딩 대기 시간 증가 (느린 페이지 고려)
        
        try:
            # 테이블 찾기
            table = WebDriverWait(driver, 20).until(  # 대기 시간 증가
                EC.presence_of_element_located((By.ID, "dataList"))
            )
            
            # 현재 페이지의 테이블 데이터 추출
            rows = table.find_elements(By.TAG_NAME, 'tr')
            
            if len(rows) <= 1:  # 헤더만 있고 데이터가 없는 경우
                print(f"[CONTRACT_CHANGE] 페이지 {current_page}에 데이터가 없습니다. 크롤링 종료.")
                break
            
            page_data = []
            stop_crawling = False
            
            for i, row in enumerate(rows):
                try:
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    if not cols or len(cols) < 12:  # 최소 12개 컬럼 필요
                        continue
                    
                    row_data = [col.text.strip() for col in cols]
                    
                    # 신청일 확인 (10번째 컬럼, 인덱스 11)
                    application_date = row_data[10] if len(row_data) > 10 else ""
                    if application_date and not application_date.startswith('2025'):
                        print(f"[CONTRACT_CHANGE] 2025년이 아닌 신청일 발견: {application_date}. 이 항목 건너뜀.")
                        continue
                    
                    # 진행상황 확인 (11번째 컬럼, 인덱스 11)
                    progress_status = row_data[11] if len(row_data) > 11 else ""
                    
                    page_data.append(row_data)
                    
                except Exception as e:
                    print(f"[CONTRACT_CHANGE] 행 데이터 추출 중 오류: {e}")
                    continue
            
            print(f"[CONTRACT_CHANGE] 페이지 {current_page}에서 {len(page_data)}개 항목 추출 완료")
            all_data.extend(page_data)
            
            # 데이터가 없으면 크롤링 종료
            if len(page_data) == 0:
                print(f"[CONTRACT_CHANGE] 페이지 {current_page}에 2025년 데이터가 없습니다. 크롤링 종료.")
                break
                
        except Exception as e:
            print(f"[CONTRACT_CHANGE] 페이지 {current_page} 크롤링 중 오류: {e}")
            break
    
    print(f"[CONTRACT_CHANGE] 총 {len(all_data)}개 항목 크롤링 완료 (2025년 신청일 조건)")
    return all_data 