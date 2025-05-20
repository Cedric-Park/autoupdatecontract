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
    driver.get(SERVICE_REQ_URL)
    try:
        table = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "dataList"))
        )
    except Exception as e:
        print('테이블 영역을 찾지 못했습니다.', e)
        return []
    
    all_data = []
    page_num = 1
    MAX_PAGES = 5  # 최대 5페이지까지만 크롤링
    
    while page_num <= MAX_PAGES:
        print(f"현재 페이지 {page_num} 크롤링 중...")
        # 현재 페이지의 테이블 데이터 추출
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
        
        # 현재 페이지 데이터를 전체 데이터에 추가
        all_data.extend(data)
        
        # 최대 페이지 수에 도달하면 종료
        if page_num >= MAX_PAGES:
            print(f"최대 페이지 수({MAX_PAGES})에 도달했습니다.")
            break
        
        # 다음 페이지가 있는지 확인
        try:
            # 다음 버튼 찾기
            next_button = None
            pagination = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
            )
            
            # 다음 페이지로 이동하는 버튼 찾기 (여러 방법 시도)
            try:
                # 방법 1: "다음" 텍스트를 포함한 링크
                next_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), '다음')]")
                if next_buttons:
                    next_button = next_buttons[0]
                else:
                    # 방법 2: ">" 기호를 포함한 링크
                    next_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), '>')]")
                    if next_buttons:
                        next_button = next_buttons[0]
                    else:
                        # 방법 3: 현재 페이지 +1 숫자를 가진 링크
                        links = pagination.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            if link.text.strip().isdigit() and int(link.text.strip()) == page_num + 1:
                                next_button = link
                                break
            except Exception as e:
                print(f"다음 버튼 찾기 오류: {e}")
            
            if not next_button:
                print("다음 페이지 버튼을 찾을 수 없습니다. 마지막 페이지로 간주합니다.")
                break
            
            # 다음 페이지로 이동
            print(f"다음 페이지({page_num + 1})로 이동 시도...")
            next_button.click()
            
            # 페이지 로딩 대기
            WebDriverWait(driver, 15).until(
                EC.staleness_of(table)
            )
            
            # 테이블 다시 찾기
            table = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "dataList"))
            )
            
            # 페이지 번호 증가
            page_num += 1
            
            # 페이지 완전 로딩을 위해 잠시 대기
            time.sleep(3)  # 대기 시간 늘림
            
        except Exception as e:
            print(f"다음 페이지 이동 중 오류 발생: {e}")
            break
    
    print(f"총 {page_num}개 페이지 크롤링 완료, {len(all_data)}개 항목 수집")
    return all_data

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
    header_len = len(header)
    # 컬럼 수에 따른 마지막 열 문자 계산 (A, B, ... Z, AA, ...)
    last_col = chr(65 + min(25, header_len - 1))  # Z까지만 처리 (26개)
    if header_len > 26:
        last_col = 'A' + chr(65 + (header_len - 1) % 26)  # AA, AB, ...

    # 번호+서비스요청명+게임사 기준으로 키 생성
    existing_keys = {}  # 키 -> 인덱스 매핑으로 변경
    for idx, row in enumerate(existing[1:], start=2):
        key = (row[0].strip(), row[3].strip(), row[4].strip())
        existing_keys[key] = idx
    
    new_rows = []
    changed_rows = []
    
    for row in filtered_data:
        key = (row[0].strip(), row[3].strip(), row[4].strip())
        
        if key in existing_keys:
            # 기존 항목인 경우 - 변경사항이 있는지 확인
            changes, changed_cols = find_and_compare_changes(sheet, row)
            if changes:
                # 변경사항이 있는 경우 업데이트
                idx = existing_keys[key]  # 해당 행의 인덱스
                
                # row 길이가 header보다 짧으면 확장
                if len(row) < header_len:
                    row = row + [''] * (header_len - len(row))
                elif len(row) > header_len:
                    row = row[:header_len]
                
                # 업데이트 범위 설정
                update_range = f'A{idx}:{last_col}{idx}'
                
                # 최신 API 형식으로 업데이트
                sheet.update(values=[row], range_name=update_range)
                changed_rows.append((row, changes, changed_cols))
                print(f"행 {idx} 업데이트: {changes}")
        else:
            # 완전 신규 항목
            # 행 길이 맞추기
            if len(row) < header_len:
                row = row + [''] * (header_len - len(row))
            elif len(row) > header_len:
                row = row[:header_len]
            
            sheet.append_row(row)
            new_rows.append(row)
            print(f"신규 행 추가: {row[0]} - {row[3]} - {row[4]}")
    
    if new_rows:
        print(f'{len(new_rows)}건 신규 업데이트 완료')
    if changed_rows:
        print(f'{len(changed_rows)}건 변경 업데이트 완료')
    if not new_rows and not changed_rows:
        print('신규/변경 업데이트 없음')
    return new_rows, changed_rows

def format_estimate_details(estimate_str):
    """
    견적서 세부 정보를 포맷팅하는 함수
    기존 형식: "주식회사 게임덱스(3,850,000 원, 2025-05-19)"
    새 형식: "1) ✔ 2025-05-19 | 주식회사 게임덱스 - 견적등록 (₩3,850,000)"
    """
    if estimate_str == "없음":
        return "없음"
    
    formatted_items = []
    estimate_items = estimate_str.split('\n')
    
    for i, item in enumerate(estimate_items, 1):
        # 기존 형식 파싱
        if '(' in item and ')' in item:
            company_part = item.split('(')[0].strip()
            details_part = item.split('(')[1].replace(')', '')
            
            # 금액과 날짜 파싱
            parts = details_part.split(', ')
            if len(parts) >= 2:
                amount = parts[0].strip()
                date = parts[1].strip()
                
                # 금액 형식 변환 (3,850,000 원 -> ₩3,850,000)
                amount = amount.replace(' 원', '')
                amount = '₩' + amount
                
                # 새 형식으로 조합
                formatted_item = f"{i}) ✔ {date} | {company_part} - 견적등록 ({amount})"
                formatted_items.append(formatted_item)
            else:
                # 파싱 실패 시 원본 그대로 유지
                formatted_items.append(f"{i}) ✔ {item}")
        else:
            # 파싱 실패 시 원본 그대로 유지
            formatted_items.append(f"{i}) ✔ {item}")
    
    return '\n'.join(formatted_items)

def make_change_alert(row, changes, changed_cols, contact_info=None):
    """
    변경 알림 메시지 생성 함수
    이메일용과 텔레그램용 메시지를 다르게 생성하고, 견적서 제출현황 등 포맷 개선
    """
    company = row[4]
    service_req = row[3]
    col_str = ', '.join(changed_cols)
    
    # 담당자 정보
    to_name = contact_info['name'] if contact_info else ""
    
    # 기본 계약 정보 (현재 값 기준)
    deadline_date = row[6]  # 입찰 마감일
    selection_date = row[7]  # 선정 마감일
    progress_status = row[8]  # 진행상황
    
    # 변경 항목 포맷팅 (견적서 제출현황은 특별 처리)
    formatted_changes = []
    estimate_changes = None
    
    for change_str in changes:
        # 변경 항목 분리
        parts = change_str.split(' : ')
        if len(parts) != 2:
            formatted_changes.append(change_str)
            continue
        
        field, value_change = parts
        field = field.strip('- ')
        
        # 입찰 마감일은 별도 처리(현재 값만 표시)
        if field == "입찰 마감일":
            # 입찰 마감일 변경 정보는 별도로 처리하지 않음
            continue
        # 견적서제출현황인 경우 특별 처리
        elif field == "견적서제출현황":
            old_val, new_val = value_change.split(' → ')
            
            # 새로운 형식으로 포맷팅
            new_formatted = format_estimate_details(new_val)
            
            # 견적서 변경 정보는 별도 섹션으로 저장
            estimate_changes = {
                "old": old_val,
                "new": new_formatted
            }
        # 그 외 일반적인 변경 항목
        else:
            formatted_changes.append(f"- {field}: {value_change}")
    
    # 이메일용 제목 및 본문
    email_title = f"[게임더하기] {company} - 계약 정보 변경 알림 [{col_str}]"
    
    # 본문 구성
    email_body = f"""
안녕하세요, {to_name}님.
게임더하기 DRIC_BOT입니다.

[{service_req}] 계약 정보에 변경 사항이 있어 알려드립니다.
게임사: {company}

계약 기본 정보:
- 입찰 마감일: {deadline_date}
- 진행상황: {progress_status}

"""
    
    # 변경 항목이 있는 경우 추가
    if formatted_changes:
        email_body += "변경된 항목:\n" + "\n".join(formatted_changes) + "\n\n"
    
    # 견적서 변경 정보가 있는 경우 별도 섹션으로 추가
    if estimate_changes:
        email_body += f"""견적서 제출 현황:
- 변경 전: {estimate_changes['old']}
- 변경 후:
{estimate_changes['new']}

"""
    
    email_body += """확인 부탁드립니다.
감사합니다."""
    
    # 텔레그램용 메시지 (더 간결하게)
    telegram_title = f"🔔 [{company}] 계약 정보 변경"
    telegram_body = f"""
{to_name}님, 게임사 [{company}]의 '{service_req}' 계약 정보가 변경되었습니다.

📅 입찰 마감일: {deadline_date}
🔄 진행상황: {progress_status}
"""
    
    # 변경 항목이 있는 경우 추가
    if formatted_changes:
        telegram_body += "\n변경된 항목:\n" + "\n".join(formatted_changes) + "\n"
    
    # 견적서 변경 정보가 있는 경우 별도 섹션으로 추가
    if estimate_changes:
        telegram_body += f"""
📋 견적서 제출 현황:
- 변경 전: {estimate_changes['old']}
- 변경 후:
{estimate_changes['new']}
"""
    
    return {
        "email_title": email_title,
        "email_body": email_body,
        "telegram_message": f"{telegram_title}\n{telegram_body}"
    }

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
                alert_info = make_change_alert(row, changes, changed_cols, company_contacts[company])
                # 이메일
                try:
                    yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_APP_PASSWORD)
                    yag.send(to=to_email, subject=alert_info["email_title"], contents=alert_info["email_body"])
                    print(f"이메일 발송 완료(변경): {to_name}({to_email})")
                except Exception as e:
                    print(f"이메일 발송 실패(변경): {to_name}({to_email}) - {e}")
                # 텔레그램
                send_telegram_message(alert_info["telegram_message"])
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