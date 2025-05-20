import gspread
from oauth2client.service_account import ServiceAccountCredentials

def test_sheets_connection():
    # 구글 시트 API 인증
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name('google_service_account.json', scope)
        client = gspread.authorize(creds)
        print('인증 성공!')
        
        # 시트 열기 시도
        try:
            sheet = client.open('게임더하기_계약관리')
            print(f'시트 열기 성공: {sheet.title}')
            
            # 워크시트 목록 확인
            worksheets = sheet.worksheets()
            print('워크시트 목록:', [ws.title for ws in worksheets])
            
            # 특정 워크시트 열기 시도
            try:
                worksheet = sheet.worksheet('게임더하기_계약_2025')
                print(f'워크시트 열기 성공: {worksheet.title}')
                
                # 데이터 읽기 테스트
                data = worksheet.get_all_values()
                print(f'데이터 읽기 성공: {len(data)} 행 있음')
                
                # 데이터 쓰기 테스트
                try:
                    # 테스트 열 찾기 (또는 추가)
                    header = data[0]
                    test_col = -1
                    if '테스트' in header:
                        test_col = header.index('테스트')
                    
                    if test_col == -1:
                        # 테스트 컬럼 추가
                        worksheet.update_cell(1, len(header) + 1, '테스트')
                        test_col = len(header)
                        print('테스트 컬럼 추가됨')
                    
                    # 테스트 데이터 쓰기
                    import time
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    worksheet.update_cell(2, test_col + 1, f'테스트 {timestamp}')
                    print('데이터 쓰기 성공!')
                except Exception as e:
                    print(f'데이터 쓰기 실패: {e}')
            except Exception as e:
                print(f'워크시트 열기 실패: {e}')
                print('사용 가능한 워크시트:', [ws.title for ws in worksheets])
        except Exception as e:
            print(f'시트 열기 실패: {e}')
            
            # 사용 가능한 시트 목록 확인
            all_sheets = client.openall()
            print('사용 가능한 시트 목록:', [s.title for s in all_sheets])
    except Exception as e:
        print(f'인증 실패: {e}')

if __name__ == '__main__':
    test_sheets_connection() 