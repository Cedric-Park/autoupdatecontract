from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import yagmail
import os
import schedule

# 모듈 import
from browser_utils import load_env, login, get_estimate_status, filter_2025_deadline
from gsheet_manager import get_gsheet, get_contact_map, get_new_company_contacts, update_gsheet
from notification import format_estimate_details, make_change_alert, send_update_emails, send_telegram_message

# 로그인 정보
SERVICE_REQ_URL = 'https://gsp.kocca.kr/admin/serviceReq/serviceReqListPage.do'

def main():
    # 환경 변수 로드
    load_env()
    
    # 브라우저 로그인
    print("\n===== 크롤링 시작 - 로그인 중 =====")
    driver = login()
    
    if driver:
        print("\n===== 로그인 성공 - 데이터 수집 시작 =====")
        all_data = []  # 모든 페이지 데이터 저장
        
        # 기본 URL 접속
        try:
            driver.get(SERVICE_REQ_URL)
            print(f"서비스 요청 페이지 접속 성공: {driver.current_url}")
        except Exception as e:
            print(f"서비스 요청 페이지 접속 실패: {e}")
            driver.quit()
            return
        
        # 최대 5페이지까지 순차적으로 처리
        MAX_PAGES = 5
        
        current_page = 1
        while current_page <= MAX_PAGES:
            print(f"\n===== 페이지 {current_page} 처리 시작 =====")
            
            # 페이지 이동 (첫 페이지는 이미 로드됨)
            if current_page > 1:
                # JavaScript 함수로 페이지 이동
                try:
                    print(f"페이지 {current_page}로 이동 중...")
                    driver.execute_script(f"go_Page({current_page})")
                    time.sleep(5)  # 페이지 전환 대기 (충분한 시간 확보)
                    
                    # 페이지 번호 확인 (현재 활성화된 페이지가 맞는지)
                    try:
                        active_page = driver.find_element(By.CSS_SELECTOR, ".pagination .active")
                        if active_page:
                            active_page_number = active_page.text.strip()
                            
                            # 페이지 번호가 일치하지 않으면 경고
                            if active_page_number != str(current_page):
                                print(f"경고: 요청한 페이지({current_page})와 실제 페이지({active_page_number})가 다릅니다.")
                                # 페이지가 일치하지 않으면 건너뛰기
                                current_page += 1
                                continue
                    except Exception:
                        # 경고 메시지 간소화
                        pass
                except Exception as e:
                    print(f"페이지 이동 실패: {e}")
                    print("더 이상 페이지를 처리할 수 없습니다. 진행 중단.")
                    break
            
            # 매 페이지마다 테이블 요소를 새로 찾는다
            try:
                print("테이블 데이터 로드 중...")
                table = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, "dataList"))
                )
                
                # 현재 페이지의 테이블 데이터 추출
                try:
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    if len(rows) <= 1:  # 헤더만 있고 데이터가 없는 경우
                        print(f"페이지에 데이터가 없습니다. 크롤링 종료.")
                        break
                    
                    print(f"테이블에서 {len(rows)-1}개 항목 발견")
                    
                    # 현재 페이지 데이터 수집
                    page_data = []
                    
                    # 각 행을 별도로 처리하여 stale element 오류 방지
                    for i in range(len(rows)):
                        try:
                            # 매번 테이블과 행을 새로 가져옴
                            table = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.ID, "dataList"))
                            )
                            current_rows = table.find_elements(By.TAG_NAME, 'tr')
                            
                            # 행 인덱스가 유효한지 확인
                            if i >= len(current_rows):
                                continue
                            
                            row = current_rows[i]
                            cols = row.find_elements(By.TAG_NAME, 'td')
                            
                            if not cols or len(cols) < 8:
                                continue
                                
                            row_data = [col.text.strip() for col in cols]
                            
                            # 견적서 제출 건이 1건 이상이면 상세페이지 진입
                            try:
                                estimate_text = cols[5].text.strip()
                                if estimate_text and estimate_text != "0건":
                                    # 매번 테이블에서 행과 셀을 다시 가져옴
                                    table = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.ID, "dataList"))
                                    )
                                    current_rows = table.find_elements(By.TAG_NAME, 'tr')
                                    if i < len(current_rows):
                                        row = current_rows[i]
                                        cols = row.find_elements(By.TAG_NAME, 'td')
                                        if len(cols) > 5:
                                            estimate_link = cols[5].find_element(By.TAG_NAME, "a")
                                            estimate_status = get_estimate_status(driver, estimate_link)
                                        else:
                                            estimate_status = "없음"
                                    else:
                                        estimate_status = "없음"
                                else:
                                    estimate_status = "없음"
                            except Exception:
                                # 에러 메시지 간소화
                                estimate_status = "없음"
                            
                            row_data.append(estimate_status)  # 견적서제출현황 컬럼 추가
                            page_data.append(row_data)
                            
                        except Exception:
                            # 에러 메시지 간소화
                            continue
                    
                    print(f"페이지 {current_page}에서 {len(page_data)}개 항목 추출 완료")
                    
                    # 2025년 입찰 마감일 필터링
                    filtered_page_data = filter_2025_deadline(page_data)
                    print(f"페이지 {current_page}에서 2025년 입찰 마감일 항목 {len(filtered_page_data)}개 필터링됨")
                    
                    # 필터링된 데이터를 전체 데이터에 추가 (중복 처리는 나중에 한번에)
                    all_data.extend(filtered_page_data)
                    
                    # 다음 페이지로
                    current_page += 1
                    
                except Exception as e:
                    print(f"페이지 {current_page} 처리 중 오류: {e}")
                    if current_page > 1:
                        print("이전에 수집된 데이터로 계속 진행")
                        current_page += 1
                    else:
                        print("첫 페이지 처리 실패, 처리 중단")
                        driver.quit()
                        return
                
            except Exception as e:
                print(f"테이블 로딩 실패: {e}")
                if current_page > 1:
                    print("이전에 수집된 데이터로 계속 진행")
                    current_page += 1
                else:
                    print("첫 페이지 처리 실패, 처리 중단")
                    driver.quit()
                    return
        
        # 모든 페이지 크롤링 완료 후 중복 데이터 제거
        print(f"\n===== 중복 데이터 제거 중 =====")
        # 번호+서비스요청명+게임사를 기준으로 중복 제거
        seen_keys = set()
        unique_data = []
        
        for row in all_data:
            if len(row) >= 5:  # 최소 5개 컬럼이 있는지 확인
                key = (row[0].strip(), row[3].strip(), row[4].strip())
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_data.append(row)
        
        print(f"총 {len(all_data)}개 항목 중 {len(unique_data)}개 고유 항목 필터링됨")
        print(f"{len(all_data) - len(unique_data)}개 중복 항목 제거됨")
        
        # 중복 제거된 데이터로 구글 시트 업데이트 (한 번만 호출)
        all_new_rows = []
        all_changed_rows = []
        
        if unique_data:
            print(f"\n===== 시트 업데이트 시작 =====")
            all_new_rows, all_changed_rows = update_gsheet(unique_data)
        
        # 모든 페이지 크롤링 완료 후 최종 결과 출력
        print(f"\n===== 크롤링 완료 =====")
        print(f"총 {len(unique_data)}개 고유 항목 처리 (2025년 입찰 마감일)")
        print(f"총 {len(all_new_rows)}개 신규 항목, {len(all_changed_rows)}개 변경 항목")
        
        # 신규/변경된 게임사별 담당자 정보 추출
        company_contacts = get_new_company_contacts(all_new_rows + [r[0] for r in all_changed_rows])
        
        # 담당자 정보가 있는 경우만 출력
        if company_contacts:
            print('\n--- 신규/변경 업데이트된 게임사별 담당자 정보 ---')
            for company, info in company_contacts.items():
                print(f'{company}: {info["name"]}')
        
        # 이메일 발송 (신규)
        if all_new_rows and company_contacts:
            send_update_emails(company_contacts, all_new_rows)
        
        # 이메일/텔레그램 알림 (변경)
        for row, changes, changed_cols in all_changed_rows:
            company = row[4]
            if company in company_contacts:
                to_name = company_contacts[company]['name']
                to_email = company_contacts[company]['email']
                alert_info = make_change_alert(row, changes, changed_cols, company_contacts[company])
                # 이메일
                try:
                    EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
                    EMAIL_APP_PASSWORD = os.environ.get('EMAIL_APP_PASSWORD')
                    yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_APP_PASSWORD)
                    yag.send(to=to_email, subject=alert_info["email_title"], contents=alert_info["email_body"])
                    print(f"이메일 발송 완료(변경): {to_name}({to_email})")
                except Exception as e:
                    print(f"이메일 발송 실패(변경): {to_name}({to_email}) - {e}")
                # 텔레그램
                send_telegram_message(alert_info["telegram_message"])
        
        driver.quit()
    else:
        print("로그인 실패, 처리 중단")

if __name__ == '__main__':
    schedule.every(1).hours.do(main)
    print("자동화 루틴이 1시간마다 실행됩니다.")
    main()  # 시작하자마자 1회 실행
    while True:
        schedule.run_pending()
        time.sleep(10) 