import os
from datetime import datetime

# 모듈화된 기능들 임포트
from browser_utils import login, crawl_all_pages_optimized
from gsheet_manager import (
    compare_and_update_optimized, 
    get_estimate_details_by_number, 
    update_estimate_details,
    get_contract_details_by_number,
    update_contract_details,
    get_gsheet,
    get_new_company_contacts,
    get_contact_map
)
from notification import send_notification, send_update_emails, make_change_alert

def send_individual_email(contact_info, alert_data):
    """
    개별 담당자에게 이메일 발송
    """
    try:
        import yagmail
        
        EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
        EMAIL_APP_PASSWORD = os.environ.get('EMAIL_APP_PASSWORD')
        
        if not EMAIL_SENDER or not EMAIL_APP_PASSWORD:
            print("❌ 이메일 환경변수가 설정되지 않았습니다.")
            return
            
        yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_APP_PASSWORD)
        yag.send(
            to=contact_info['email'],
            subject=alert_data['email_title'],
            contents=alert_data['email_body']
        )
        print(f"📧 개별 이메일 발송 완료: {contact_info['name']}({contact_info['email']})")
        
    except Exception as e:
        print(f"❌ 개별 이메일 발송 실패: {e}")

def send_new_contract_notifications(new_rows):
    """
    신규 계약 알림 통합 처리
    """
    if not new_rows:
        return
        
    print(f"\n🔔 신규 계약 알림 처리 시작: {len(new_rows)}건")
    
    # 1. 담당자 개별 이메일 발송
    company_contacts = get_new_company_contacts(new_rows)
    if company_contacts:
        send_update_emails(company_contacts, new_rows)
        print(f"📧 신규 계약 개별 이메일 발송: {len(company_contacts)}개 게임사")
    
    # 2. 관리자 알림 - 전체 요약과 게임사별 개별 알림
    companies_with_contact = list(company_contacts.keys()) if company_contacts else []
    companies_without_contact = [row[4] for row in new_rows if row[4] not in companies_with_contact]
    
    # 전체 요약 알림
    summary_message = f"""🆕 신규 계약 등록 알림

총 {len(new_rows)}건의 신규 계약이 등록되었습니다.

담당자 있는 게임사 ({len(companies_with_contact)}건):
{', '.join(companies_with_contact) if companies_with_contact else '없음'}

담당자 없는 게임사 ({len(companies_without_contact)}건):
{', '.join(companies_without_contact) if companies_without_contact else '없음'}

상세 내용은 구글 시트를 확인해주세요."""
    
    send_notification(summary_message)
    print("📱 신규 계약 요약 관리자 알림 발송")
    
    # 3. 게임사별 개별 상세 알림 (담당자가 있는 경우만)
    contact_map = get_contact_map()
    for row in new_rows:
        company = row[4]
        service_req = row[3]
        
        if company in contact_map:
            # 담당자가 있는 게임사에 대한 개별 상세 알림
            contact_info = contact_map[company]
            
            individual_message = f"""🔔 [{company}] 신규 계약 업데이트

{contact_info['name']}님, 게임사 [{company}]에서 신규 계약이 등록되었습니다.

📋 계약 정보:
- 서비스 부문: {row[1]}
- 서비스 요청명: {service_req}
- 입찰 마감일: {row[6]}
- 제출된 견적서: {row[5]}
- 진행상황: {row[8]}

확인 부탁드립니다."""
            
            send_notification(individual_message)
            print(f"📱 개별 신규 계약 알림 발송: {company}")
    
    print(f"📱 신규 계약 관리자 텔레그램 알림 완료")

def send_change_notifications(updated_rows):
    """
    변경사항 알림 통합 처리
    """
    if not updated_rows:
        return
        
    print(f"\n🔔 변경사항 알림 처리 시작: {len(updated_rows)}건")
    
    contact_map = get_contact_map()
    sheet = get_gsheet()  # 시트 연결 추가
    
    # 알림 발송 통계
    email_sent = 0
    telegram_sent = 0
    
    for item in updated_rows:
        company = item['crawled_data'][4]
        service_req = item['crawled_data'][3]
        contact_info = contact_map.get(company)
        row_index = item['row_index']
        
        # 견적서 정보가 변경된 경우 J열에서 최신 견적서 상세 정보 가져오기
        estimate_details = None
        if item.get('estimate_count_changed'):
            try:
                # J열 (10번째 열) 값 가져오기 (1-indexed이므로 row_index 그대로 사용)
                estimate_cell_value = sheet.cell(row_index, 10).value
                if estimate_cell_value and estimate_cell_value.strip() and estimate_cell_value != "없음":
                    estimate_details = estimate_cell_value
                    print(f"📋 견적서 상세 정보 추가: 행 {row_index}")
            except Exception as e:
                print(f"❌ 견적서 정보 읽기 실패: 행 {row_index} - {e}")
        
        if contact_info:
            # 담당자가 있는 경우: 개별 이메일 + 관리자 텔레그램
            try:
                alert_data = make_change_alert(
                    item['crawled_data'], 
                    item['changes'], 
                    item['changed_cols'], 
                    contact_info,
                    estimate_details  # 견적서 상세 정보 추가
                )
                
                # 개별 이메일 발송
                send_individual_email(contact_info, alert_data)
                email_sent += 1
                
                # 관리자 텔레그램 발송
                send_notification(alert_data['telegram_message'])
                telegram_sent += 1
                
                print(f"✅ 변경 알림 발송 완료: {company} - {service_req}")
                
            except Exception as e:
                print(f"❌ 변경 알림 발송 실패: {company} - {e}")
    
    print(f"📧 변경사항 개별 이메일 발송: {email_sent}건")
    print(f"📱 변경사항 관리자 텔레그램 발송: {telegram_sent}건")

def main():
    print("🚀 최적화된 자동화 시스템 시작")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 브라우저 로그인
    print("📱 브라우저 로그인 중...")
    driver = login()
    if not driver:
        print("❌ 로그인 실패. 프로그램을 종료합니다.")
        return
    
    try:
        print("✅ 로그인 성공!")
        
        # 최적화된 크롤링 시작
        print("\n🔍 최적화된 크롤링 시작 (최대 10페이지, 2025년 조건부 중단)")
        print("-" * 50)
        
        crawled_data = crawl_all_pages_optimized(driver)
        
        if not crawled_data:
            print("❌ 크롤링된 데이터가 없습니다.")
            return
        
        print(f"✅ 크롤링 완료: 총 {len(crawled_data)}개 항목")
        print(f"   - 모든 항목이 2025년 입찰 마감일 조건 충족")
        
        # 최적화된 비교 및 업데이트
        print("\n📊 데이터 비교 및 업데이트 시작")
        print("-" * 50)
        
        new_rows, updated_rows = compare_and_update_optimized(crawled_data)
        
        # 상세 정보 업데이트 처리 (우선순위 기반)
        estimate_update_count = 0
        contract_update_count = 0
        
        for item in updated_rows:
            estimate_number = item.get('estimate_number')
            row_index = item['row_index']
            
            if not estimate_number:
                continue
                
            sheet = get_gsheet()
            
            # 1순위: 최종계약체결 - 모든 상세 정보 업데이트
            if item.get('progress_changed') and item.get('is_final_contract'):
                print(f"🏆 최종계약체결 감지: 행 {row_index}, 넘버 {estimate_number}")
                
                # 견적서 상세 정보 추출 (J열)
                estimate_details = get_estimate_details_by_number(driver, estimate_number)
                if estimate_details and estimate_details != "없음":
                    update_estimate_details(sheet, row_index, estimate_details)
                    estimate_update_count += 1
                
                # 계약 상세 정보 추출 (K,L,M,N열)
                contract_details = get_contract_details_by_number(driver, estimate_number)
                if contract_details:
                    update_contract_details(sheet, row_index, contract_details)
                    contract_update_count += 1
                    
            # 2순위: 견적서 건수 변경 (최종계약체결이 아닌 경우)
            elif item.get('estimate_count_changed') and not item.get('is_final_contract'):
                print(f"📋 견적서 건수 변경 감지: 행 {row_index}, 넘버 {estimate_number}")
                
                # 견적서 상세 정보만 추출 (J열)
                estimate_details = get_estimate_details_by_number(driver, estimate_number)
                if estimate_details and estimate_details != "없음":
                    update_estimate_details(sheet, row_index, estimate_details)
                    estimate_update_count += 1
        
        # 🔔 알림 처리
        print("\n" + "=" * 60)
        print("🔔 알림 처리 시작")
        print("=" * 60)
        
        # 신규 계약 알림
        send_new_contract_notifications(new_rows)
        
        # 변경사항 알림
        send_change_notifications(updated_rows)
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📈 최종 결과 요약")
        print("=" * 60)
        print(f"🆕 신규 추가된 항목: {len(new_rows)}건")
        print(f"🔄 변경 업데이트 항목: {len(updated_rows)}건")
        print(f"📋 견적서 상세 업데이트: {estimate_update_count}건")
        print(f"🏆 계약 상세 업데이트: {contract_update_count}건")
        print(f"🎯 총 크롤링 범위: {len(crawled_data)}개 항목 (2025년 한정)")
        
        # 변경사항 상세 로그
        if updated_rows:
            print("\n📝 변경사항 상세:")
            for item in updated_rows:
                crawled_data = item['crawled_data']
                changes = item['changes']
                print(f"   📄 {crawled_data[0]} ({crawled_data[3]})")
                for change in changes:
                    print(f"     {change}")
        
    except Exception as e:
        error_message = f"❌ 프로그램 실행 중 오류 발생: {e}"
        print(error_message)
        send_notification(error_message)
        
    finally:
        if driver:
            driver.quit()
            print("\n🔄 브라우저 종료 완료")
        
        print("\n🏁 프로그램 실행 완료")

if __name__ == "__main__":
    main() 