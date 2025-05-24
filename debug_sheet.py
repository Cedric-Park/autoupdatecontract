import gspread
from oauth2client.service_account import ServiceAccountCredentials

def debug_sheet_structure():
    """구글 시트 구조 디버깅"""
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name('google_service_account.json', scope)
        client = gspread.authorize(creds)
        
        sheet = client.open('게임더하기_계약관리').worksheet('게임더하기_계약_2025')
        
        print("=== 구글 시트 구조 분석 ===")
        
        # 전체 데이터 가져오기
        all_values = sheet.get_all_values()
        print(f"총 행 수: {len(all_values)}")
        
        if len(all_values) > 0:
            # 헤더 행 확인
            header_row = all_values[0]
            print(f"헤더 행 컬럼 수: {len(header_row)}")
            print(f"실제 데이터가 있는 헤더:")
            
            for i, header in enumerate(header_row[:20]):  # 처음 20개만 확인
                if header.strip():
                    print(f"  {chr(65+i)}({i+1}): {header}")
        
        # 데이터 행들 확인
        if len(all_values) > 1:
            print(f"\n데이터 행 분석:")
            for row_idx in range(1, min(6, len(all_values))):  # 처음 5개 데이터 행만
                row = all_values[row_idx]
                print(f"  행 {row_idx+1}: 컬럼수={len(row)}")
                
                # 비어있지 않은 셀들만 출력
                non_empty = []
                for i, cell in enumerate(row[:15]):  # 처음 15개만
                    if cell.strip():
                        non_empty.append(f"{chr(65+i)}:{cell}")
                
                if non_empty:
                    print(f"    데이터: {', '.join(non_empty)}")
                else:
                    print(f"    모든 셀이 비어있음")
        
        # 시트의 실제 사용 범위 확인
        try:
            # 마지막으로 사용된 행과 열 확인
            used_range = sheet.get('A1:Z1000')  # Z열까지, 1000행까지 확인
            last_row_with_data = 0
            last_col_with_data = 0
            
            for row_idx, row in enumerate(used_range):
                for col_idx, cell in enumerate(row):
                    if cell.strip():
                        last_row_with_data = max(last_row_with_data, row_idx + 1)
                        last_col_with_data = max(last_col_with_data, col_idx + 1)
            
            print(f"\n실제 사용 범위:")
            print(f"  마지막 데이터 행: {last_row_with_data}")
            print(f"  마지막 데이터 열: {chr(64+last_col_with_data)}({last_col_with_data})")
            
        except Exception as e:
            print(f"사용 범위 확인 중 오류: {e}")
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    debug_sheet_structure() 