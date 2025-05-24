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
    get_gsheet
)
from notification import send_notification

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