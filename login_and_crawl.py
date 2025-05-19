from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict
import yagmail
import os
from dotenv import load_dotenv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import schedule

# 로그인 정보
LOGIN_URL = 'https://gsp.kocca.kr/admin'
SERVICE_REQ_URL = 'https://gsp.kocca.kr/admin/serviceReq/serviceReqListPage.do'
USER_ID = 'com2us30'
USER_PW = 'com2us!@#$'

# 크롬 드라이버 설정
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 브라우저 창을 띄우지 않음
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

SHEET_NAME = '게임더하기_계약관리'  # 실제 구글 시트 문서명으로 수정
WORKSHEET_NAME = '게임더하기_계약_2025'  # 실제 워크시트명으로 수정
GOOGLE_CREDENTIALS_FILE = 'google_service_account.json'  # 서비스 계정 키 파일명
CONTACT_SHEET_NAME = '담당자정보'  # 담당자 정보 시트명

# .env 파일에서 환경변수 불러오기
def load_env():
    load_dotenv()

def login():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(LOGIN_URL)
    time.sleep(2)  # 페이지 로딩 대기

    # 로그인 폼이 실제로 존재하는지 체크
    try:
        id_input = driver.find_element(By.ID, 'j_username')
        pw_input = driver.find_element(By.ID, 'j_password')
        # 로그인 폼이 있으면 로그인 시도
        id_input.send_keys(USER_ID)
        pw_input.send_keys(USER_PW)
        pw_input.send_keys(Keys.RETURN)
        time.sleep(2)
        print('로그인 시도 완료')
    except Exception:
        # 로그인 폼이 없으면 이미 로그인 상태로 간주
        print('로그인 폼이 없어 이미 로그인 상태로 간주합니다.')

    # 로그인 성공 여부를 관리자 페이지 URL로 명확히 확인
    if 'admin' in driver.current_url and 'login' not in driver.current_url:
        print('로그인 성공!')
        return driver
    else:
        print('로그인 실패 또는 세션 만료!')
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
        협력사 = dtds[1].text.strip()
        견적일자 = dtds[3].text.strip()
        견적금액 = dtds[4].text.strip()
        estimates.append(f"{협력사}({견적금액}, {견적일자})")
    # 원래 페이지로 복귀
    driver.back()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "dataList"))
    )
    time.sleep(1)
    return '\n'.join(estimates) if estimates else "없음"

def crawl_service_req_table_with_estimate(driver):
    driver.get(SERVICE_REQ_URL)
    try:
        table = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "dataList"))
        )
    except Exception as e:
        print('테이블 영역을 찾지 못했습니다.', e)
        return []
    rows = table.find_elements(By.TAG_NAME, 'tr')
    data = []
    for i, row in enumerate(rows):
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
        except Exception:
            estimate_status = "없음"
        row_data.append(estimate_status)  # 견적서제출현황 컬럼 추가
        data.append(row_data)
    return data

def filter_2025_deadline(data):
    filtered = []
    for row in data:
        if len(row) < 7:
            continue
        deadline = row[6]  # 7번째 컬럼: 입찰 마감일
        if deadline.startswith('2025'):
            filtered.append(row)
    return filtered

# 구글 시트 인증 및 시트 객체 반환
def get_gsheet():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
    return sheet

def get_contact_map():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    contact_sheet = client.open(SHEET_NAME).worksheet(CONTACT_SHEET_NAME)
    rows = contact_sheet.get_all_values()
    contact_map = {}
    for row in rows[1:]:  # 첫 행은 헤더
        if len(row) >= 3:
            company, name, email = row[0].strip(), row[1].strip(), row[2].strip()
            contact_map[company] = {'name': name, 'email': email}
    return contact_map

# 신규 업데이트된 게임사별 담당자 정보 추출
def get_new_company_contacts(new_rows):
    contact_map = get_contact_map()
    company_to_contact = {}
    for row in new_rows:
        if len(row) >= 5:
            company = row[4]
            if company in contact_map:
                company_to_contact[company] = contact_map[company]
    return company_to_contact

def find_and_compare_changes(sheet, new_row):
    existing = sheet.get_all_values()
    header = existing[0]  # 첫 행이 컬럼명
    for row in existing[1:]:
        # 번호 + 서비스 요청명 + 게임사 기준으로 매칭
        if row[0].strip() == new_row[0].strip() and row[3].strip() == new_row[3].strip() and row[4].strip() == new_row[4].strip():
            changes = []
            changed_cols = []
            for i, (old, new) in enumerate(zip(row, new_row)):
                if old.strip() != new.strip():
                    changes.append(f"- {header[i]} : {old.strip()} → {new.strip()}")
                    changed_cols.append(header[i])
            return changes, changed_cols
    return None, None

# update_gsheet 함수에서 신규 row 추가 대신 변경 row는 수정, 변경 내역 반환

def update_gsheet(filtered_data):
    sheet = get_gsheet()
    existing = sheet.get_all_values()
    header = existing[0]
    # 번호+서비스요청명+게임사 기준으로 중복 체크
    existing_keys = set((row[0].strip(), row[3].strip(), row[4].strip()) for row in existing[1:])
    new_rows = []
    changed_rows = []
    for row in filtered_data:
        key = (row[0].strip(), row[3].strip(), row[4].strip())
        if key not in existing_keys:
            # 기존 row와 번호+서비스요청명+게임사로 매칭해 변경 내역 확인
            changes, changed_cols = find_and_compare_changes(sheet, row)
            if changes:
                # 기존 row 수정(값 갱신)
                for idx, old_row in enumerate(existing[1:], start=2):  # 2행부터
                    if old_row[0].strip() == row[0].strip() and old_row[3].strip() == row[3].strip() and old_row[4].strip() == row[4].strip():
                        sheet.update(f'A{idx}:I{idx}', [row])
                        changed_rows.append((row, changes, changed_cols))
                        break
            else:
                # 완전 신규 row 추가
                sheet.append_row(row)
                new_rows.append(row)
    if new_rows:
        print(f'{len(new_rows)}건 신규 업데이트 완료')
    if changed_rows:
        print(f'{len(changed_rows)}건 변경 업데이트 완료')
    if not new_rows and not changed_rows:
        print('신규/변경 업데이트 없음')
    return new_rows, changed_rows

# 알림 메시지 생성 함수

def make_change_alert(row, changes, changed_cols):
    company = row[4]
    service_req = row[3]
    col_str = ', '.join(changed_cols)
    title = f"[게임더하기] {company} - 계약 정보 변경 알림 [{col_str}]"
    body = f"[{service_req}/{company}] 계약 정보가 변경되었습니다.\n" + '\n'.join(changes)
    return title, body

# 신규 계약 담당자에게 이메일 발송
def send_update_emails(company_contacts, new_rows):
    print('이메일 발송 대상:', company_contacts)
    print('신규 업데이트 데이터:', new_rows)
    if not company_contacts:
        print('이메일 발송 대상 없음')
        return
    yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_APP_PASSWORD)
    for row in new_rows:
        if len(row) < 5:
            continue
        company = row[4]
        if company not in company_contacts:
            continue
        contact = company_contacts[company]
        to_email = contact['email']
        to_name = contact['name']
        subject = f"[게임더하기] {company} 신규 계약 [{row[3]}] 업데이트 알림"
        body = f"""
{to_name}님, 안녕하세요.
게임더하기 DRIC_BOT입니다.

게임사 [{company}]에서 신규 계약(서비스 부문: {row[1]})이 업데이트 되었습니다.\n\n- 서비스 요청명: {row[3]}\n- 입찰 마감일: {row[6]}\n- 제출된 견적서 : {row[5]}\n- 진행상황: {row[8]}\n
확인 부탁드립니다.

감사합니다.
"""
        try:
            yag.send(to=to_email, subject=subject, contents=body)
            print(f"이메일 발송 완료: {to_name}({to_email})")
        except Exception as e:
            print(f"이메일 발송 실패: {to_name}({to_email}) - {e}")

def send_telegram_message(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        print('텔레그램 토큰 또는 채널 ID가 설정되어 있지 않습니다.')
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("텔레그램 알림 전송 완료")
    else:
        print("텔레그램 알림 실패:", response.text)

def main():
    load_env()
    global EMAIL_SENDER, EMAIL_APP_PASSWORD
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
    EMAIL_APP_PASSWORD = os.environ.get('EMAIL_APP_PASSWORD')
    driver = login()
    if driver:
        table_data = crawl_service_req_table_with_estimate(driver)
        filtered_data = filter_2025_deadline(table_data)
        print('--- 2025년 입찰 마감일 항목 ---')
        for row in filtered_data:
            print(row)
        new_rows, changed_rows = update_gsheet(filtered_data)
        # 신규 업데이트된 게임사별 담당자 정보 추출
        company_contacts = get_new_company_contacts(new_rows + [r[0] for r in changed_rows])
        print('--- 신규/변경 업데이트된 게임사별 담당자 정보 ---')
        for company, info in company_contacts.items():
            print(f'{company}: {info}')
        # 이메일 발송 (신규)
        send_update_emails(company_contacts, new_rows)
        # 이메일/텔레그램 알림 (변경)
        for row, changes, changed_cols in changed_rows:
            company = row[4]
            if company in company_contacts:
                to_name = company_contacts[company]['name']
                to_email = company_contacts[company]['email']
                title, body = make_change_alert(row, changes, changed_cols)
                # 이메일
                try:
                    yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_APP_PASSWORD)
                    yag.send(to=to_email, subject=title, contents=body)
                    print(f"이메일 발송 완료(변경): {to_name}({to_email})")
                except Exception as e:
                    print(f"이메일 발송 실패(변경): {to_name}({to_email}) - {e}")
                # 텔레그램
                send_telegram_message(f"{title}\n{body}")
        # 텔레그램 알림 (신규)
        for row in new_rows:
            if len(row) >= 5:
                company = row[4]
                if company in company_contacts:
                    to_name = company_contacts[company]['name']
                    message = f"{to_name}님, 게임사 [{company}]에서 현재 [{row[1]} - {row[3]}] 계약이 업데이트 되었습니다."
                    send_telegram_message(message)
        driver.quit()

if __name__ == '__main__':
    schedule.every(1).hours.do(main)
    print("자동화 루틴이 1시간마다 실행됩니다.")
    main()  # 시작하자마자 1회 실행
    while True:
        schedule.run_pending()
        time.sleep(10) 