import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

SHEET_NAME = '게임더하기_계약관리'  # 실제 구글 시트 문서명으로 수정
WORKSHEET_NAME = '게임더하기_계약_2025'  # 실제 워크시트명으로 수정
GOOGLE_CREDENTIALS_FILE = 'google_service_account.json'  # 서비스 계정 키 파일명
CONTACT_SHEET_NAME = '담당자정보'  # 담당자 정보 시트명

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

def find_and_compare_changes_without_api(existing_row, new_row, header):
    """
    API 호출 없이 로컬에서 변경사항을 비교하는 함수
    """
    # 디버깅 메시지 제거
    # print(f"항목 비교 시작: {existing_row[0].strip()} - {existing_row[3].strip()}")
    
    # 번호 + 서비스 요청명 + 게임사 기준으로 매칭
    if existing_row[0].strip() == new_row[0].strip() and existing_row[3].strip() == new_row[3].strip() and existing_row[4].strip() == new_row[4].strip():
        changes = []
        changed_cols = []
        
        # 실제 컬럼 인덱스와 의미 (중요한 필드들)
        important_fields = {
            5: "견적서제출건수",  # 6번째 컬럼: 견적서 제출 건수
            8: "진행상황",      # 9번째 컬럼: 진행상황
            9: "견적서제출현황"   # 10번째 컬럼: 견적서제출현황 (우리가 추가한 컬럼)
        }
        
        # 중요 필드 값 확인하되 상세 출력은 변경 필드만
        changed_important_fields = []
        for idx, field_name in important_fields.items():
            if idx < len(existing_row) and idx < len(new_row):
                old_val = existing_row[idx].strip() if idx < len(existing_row) else ""
                new_val = new_row[idx].strip() if idx < len(new_row) else ""
                is_changed = old_val != new_val
                
                if is_changed:
                    changed_important_fields.append(field_name)
                    # 중요 필드는 header 상관없이 우리가 알고 있는 이름으로 지정
                    header_name = header[idx] if idx < len(header) else field_name
                    changes.append(f"- {header_name} : {old_val} → {new_val}")
                    changed_cols.append(header_name)
        
        # 중요 필드 변경 내용 출력 (있을 경우만)
        if changed_important_fields:
            print(f"중요 필드 변경 감지: {', '.join(changed_important_fields)}")
        
        # 그 외 모든 필드 비교
        other_changed_fields = []
        for i, (old, new) in enumerate(zip(existing_row, new_row)):
            # 이미 중요 필드로 체크한 것은 건너뜀
            if i in important_fields:
                continue
                
            if i < len(header):
                old_val = old.strip()
                new_val = new.strip()
                
                # 비교할 때 공백 제거하고 비교
                if old_val != new_val:
                    field_name = header[i] if i < len(header) else f"컬럼{i+1}"
                    other_changed_fields.append(field_name)
                    changes.append(f"- {field_name} : {old_val} → {new_val}")
                    changed_cols.append(field_name)
        
        # 그 외 필드 변경 내용 출력 (있을 경우만)
        if other_changed_fields:
            print(f"기타 필드 변경 감지: {', '.join(other_changed_fields)}")
            
        # 변경사항 요약 (있을 경우만)
        if changes:
            print(f"총 {len(changes)}개 항목 변경 감지")
            return changes, changed_cols
        return None, None
    return None, None

def find_and_compare_changes(sheet, new_row):
    """
    API 호출을 통해 변경사항을 비교하는 함수 (기존 방식)
    """
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

def update_gsheet(filtered_data):
    try:
        sheet = get_gsheet()
        print("Google 시트 데이터 로드 중...")
        
        # 시트 데이터를 한 번만 가져오기
        existing = sheet.get_all_values()
        print(f"기존 데이터 {len(existing)-1}개 항목 로드 완료")
        
        header = existing[0]
        header_len = len(header)
        # 컬럼 수에 따른 마지막 열 문자 계산 (A, B, ... Z, AA, ...)
        last_col = chr(65 + min(25, header_len - 1))  # Z까지만 처리 (26개)
        if header_len > 26:
            last_col = 'A' + chr(65 + (header_len - 1) % 26)  # AA, AB, ...

        # 번호+서비스요청명+게임사 기준으로 키 생성
        existing_keys = {}  # 키 -> 인덱스 매핑으로 변경
        existing_data = {}  # 키 -> 행 데이터 매핑 (디버깅용)
        for idx, row in enumerate(existing[1:], start=2):
            if len(row) >= 5:  # 최소 5개 컬럼이 있는지 확인
                key = (row[0].strip(), row[3].strip(), row[4].strip())
                existing_keys[key] = idx
                existing_data[key] = row
        
        print(f"기존 데이터 키 매핑 완료")
        
        new_rows = []
        changed_rows = []
        
        # API 호출 간 지연 시간
        API_DELAY = 2  # 초
        
        for i, row in enumerate(filtered_data):
            # 처리 중인 항목 표시 (5개 단위로)
            if i > 0 and i % 5 == 0:
                print(f"총 {len(filtered_data)}개 중 {i}개 항목 처리 완료...")
            
            if len(row) < 5:
                continue
                
            key = (row[0].strip(), row[3].strip(), row[4].strip())
            item_id = row[0].strip() if len(row) > 0 else "알 수 없음"
            
            if key in existing_keys:
                # 기존 항목인 경우 - 변경사항이 있는지 확인
                ex_row = existing[existing_keys[key]-1]
                changes, changed_cols = find_and_compare_changes_without_api(ex_row, row, header)
                
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
                    print(f"항목 {item_id} 업데이트 완료")
                    
                    # API 할당량 초과 방지를 위한 지연
                    time.sleep(API_DELAY)
            else:
                # 완전 신규 항목
                print(f"신규 항목 발견: ID={item_id}")
                
                # 행 길이 맞추기
                if len(row) < header_len:
                    row = row + [''] * (header_len - len(row))
                elif len(row) > header_len:
                    row = row[:header_len]
                
                # 신규 행 요약 출력 (간소화)
                print(f"신규 항목 {item_id} 추가 중...")
                
                # 행 추가
                sheet.append_row(row)
                new_rows.append(row)
                print(f"신규 항목 {item_id} 추가 완료")
                
                # API 할당량 초과 방지를 위한 지연
                time.sleep(API_DELAY)
        
        print("\n===== 시트 업데이트 결과 =====")
        if new_rows:
            print(f'{len(new_rows)}건 신규 업데이트 완료')
        if changed_rows:
            print(f'{len(changed_rows)}건 변경 업데이트 완료')
        if not new_rows and not changed_rows:
            print('신규/변경 업데이트 없음')
        return new_rows, changed_rows
        
    except gspread.exceptions.APIError as e:
        if "429" in str(e):
            print("Google Sheets API 할당량이 초과되었습니다. 잠시 후 다시 시도합니다.")
            time.sleep(60)  # 1분 대기 후 재시도
            return update_gsheet(filtered_data)  # 재귀적으로 다시 시도
        else:
            print(f"Google Sheets API 오류: {e}")
            return [], []
    except Exception as e:
        print(f"시트 업데이트 중 오류 발생: {e}")
        return [], [] 