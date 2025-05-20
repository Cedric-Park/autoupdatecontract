import gspread
from oauth2client.service_account import ServiceAccountCredentials
from login_and_crawl import get_gsheet, find_and_compare_changes

def test_update_functionality():
    # 구글 시트 연결
    sheet = get_gsheet()
    print("시트 연결 성공")
    
    # 현재 데이터 확인
    existing = sheet.get_all_values()
    header = existing[0]
    print(f"헤더 정보: {header}")
    print(f"데이터 행 수: {len(existing)-1}")
    
    # 첫 번째 데이터 행 가져오기 (테스트용)
    if len(existing) > 1:
        test_row = existing[1]
        print(f"테스트용 행: {test_row}")
        
        # 테스트 데이터 생성 (원본 데이터에서 약간 변경)
        import copy
        modified_row = copy.deepcopy(test_row)
        modified_row[-1] = "테스트 변경 " + modified_row[-1]
        
        # 변경 감지 테스트
        changes, changed_cols = find_and_compare_changes(sheet, modified_row)
        print("변경 감지 결과:")
        print(f"변경 내용: {changes}")
        print(f"변경 컬럼: {changed_cols}")
        
        # 구글 시트에 직접 업데이트 시도
        try:
            if changes:
                # 변경 행에 맞는 인덱스 찾기
                for idx, old_row in enumerate(existing[1:], start=2):
                    if (old_row[0].strip() == test_row[0].strip() and 
                        old_row[3].strip() == test_row[3].strip() and 
                        old_row[4].strip() == test_row[4].strip()):
                        
                        # 기존 함수의 업데이트 로직과 동일하게 시도
                        sheet.update(f'A{idx}:I{idx}', [modified_row])
                        print(f"구글 시트 {idx}행 직접 업데이트 완료")
                        break
            else:
                print("감지된 변경사항 없음")
        except Exception as e:
            print(f"구글 시트 업데이트 실패: {e}")
    else:
        print("테스트할 데이터가 없습니다.")

if __name__ == "__main__":
    test_update_functionality() 