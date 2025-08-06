import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re

SHEET_NAME = '게임더하기_계약관리'  # 실제 구글 시트 문서명으로 수정
WORKSHEET_NAME = '게임더하기_계약_2025'  # 실제 워크시트명으로 수정
GOOGLE_CREDENTIALS_FILE = 'google_service_account.json'  # 서비스 계정 키 파일명
CONTACT_SHEET_NAME = '담당자정보'  # 담당자 정보 시트명

# 특수 문자 처리 함수 추가
def sanitize_text(text):
    """
    특수 문자를 CP949에서 호환되는 문자로 변환
    """
    if not text:
        return text
        
    # 특수 대시(–, \u2013) → 일반 하이픈(-)
    text = text.replace('\u2013', '-')
    # 특수 따옴표(' ', " ") → 일반 따옴표(', ")
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    # 특수 공백 → 일반 공백
    text = text.replace('\u00a0', ' ')
    # 기타 특수 문자 제거
    text = re.sub(r'[\u2000-\u206F]', '', text)
    
    return text

# 구글 시트 인증 및 시트 객체 반환
def get_gsheet():
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
        ]
        print(f"[AUTH] 구글 시트 인증 시작...")
        print(f"[INFO] 인증 파일: {GOOGLE_CREDENTIALS_FILE}")
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        
        print(f"[SHEET] 시트 문서 열기: {SHEET_NAME}")
        spreadsheet = client.open(SHEET_NAME)
        
        print(f"[ESTIMATE] 워크시트 선택: {WORKSHEET_NAME}")
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        print(f"[OK] 구글 시트 연결 성공!")
        print(f"   - 시트 ID: {spreadsheet.id}")
        print(f"   - 워크시트 ID: {sheet.id}")
        print(f"   - 워크시트 제목: {sheet.title}")
        
        return sheet
        
    except Exception as e:
        print(f"[ERROR] 구글 시트 연결 실패: {e}")
        print(f"   - 시트명: {SHEET_NAME}")
        print(f"   - 워크시트명: {WORKSHEET_NAME}")
        print(f"   - 인증파일: {GOOGLE_CREDENTIALS_FILE}")
        raise

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

        # 번호+게임사 기준으로 키 생성 (서비스요청명 제외)
        existing_keys = {}  # 키 -> 인덱스 매핑으로 변경
        existing_data = {}  # 키 -> 행 데이터 매핑 (디버깅용)
        for idx, row in enumerate(existing[1:], start=2):
            if len(row) >= 5:  # 최소 5개 컬럼이 있는지 확인
                key = (row[0].strip(), row[4].strip())  # 번호와 게임사만으로 고유키 생성
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
                
            key = (row[0].strip(), row[4].strip())  # 번호와 게임사만으로 고유키 생성
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
                # 완전 신규 항목 (번호-게임사 기준)
                print(f"신규 항목 발견: 번호 {item_id} - 게임사 {row[4] if len(row) > 4 else 'N/A'}")
                
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

def compare_and_update_optimized(crawled_data, driver):
    """
    최적화된 비교 및 업데이트: 구글시트 전체 데이터와 크롤링 데이터 비교 후 변경사항만 업데이트
    + 숨겨진 변경(견적 상세) 감지 기능 추가
    """
    try:
        sheet = get_gsheet()
        print("구글 시트 전체 데이터 로드 중...")
        
        # 시트 데이터를 한 번만 가져오기
        existing = sheet.get_all_values()
        print(f"기존 데이터 {len(existing)-1}개 항목 로드 완료")
        
        if len(existing) <= 1:  # 헤더만 있는 경우
            print("구글 시트에 데이터가 없습니다. 모든 크롤링 데이터를 신규 추가합니다.")
            return add_all_new_data(sheet, crawled_data)
        
        header = existing[0]
        header_len = len(header)
        
        # 기존 데이터를 키 기반으로 매핑 (번호+게임사)
        existing_data_map = {}
        for idx, row in enumerate(existing[1:], start=2):
            if len(row) >= 5:
                key = (row[0].strip(), row[4].strip())  # 번호와 게임사만으로 고유키 생성
                existing_data_map[key] = {
                    'row_index': idx,
                    'data': row,
                    'estimate_number': row[10] if len(row) > 10 else ""  # 견적서 넘버
                }
        
        print(f"기존 데이터 키 매핑 완료: {len(existing_data_map)}개 항목")
        
        # 변경사항 분석
        new_rows = []
        changed_rows = []
        
        for crawled_row in crawled_data:
            if len(crawled_row) < 5:
                continue
                
            key = (crawled_row[0].strip(), crawled_row[4].strip())  # 번호와 게임사만으로 고유키 생성
            
            if key in existing_data_map:
                # 기존 항목 - 변경사항 확인
                existing_item = existing_data_map[key]
                existing_row = existing_item['data']
                
                changes = []
                changed_cols = []
                
                # 0-8번째 컬럼 비교 (기본 데이터)
                for i in range(min(9, len(existing_row), len(crawled_row))):
                    old_val = existing_row[i].strip() if i < len(existing_row) else ""
                    new_val = crawled_row[i].strip() if i < len(crawled_row) else ""
                    
                    if old_val != new_val:
                        field_name = header[i] if i < len(header) else f"컬럼{i+1}"
                        changes.append(f"- {field_name} : {old_val} → {new_val}")
                        changed_cols.append(field_name)
                
                if changes:
                    print(f"변경사항 감지: {key[0]} - {', '.join(changed_cols)}")
                    
                    # 견적서 제출 건수(5번째) 변경 확인
                    estimate_count_changed = False
                    if len(crawled_row) > 5 and len(existing_row) > 5:
                        if existing_row[5].strip() != crawled_row[5].strip():
                            estimate_count_changed = True
                    
                    # 진행상황(8번째) 변경 및 최종계약체결 확인
                    progress_changed = False
                    is_final_contract = False
                    if len(crawled_row) > 8 and len(existing_row) > 8:
                        if existing_row[8].strip() != crawled_row[8].strip():
                            progress_changed = True
                        if crawled_row[8].strip() == "최종계약체결":
                            is_final_contract = True
                    
                    changed_rows.append({
                        'row_index': existing_item['row_index'],
                        'crawled_data': crawled_row,
                        'changes': changes,
                        'changed_cols': changed_cols,
                        'estimate_count_changed': estimate_count_changed,
                        'progress_changed': progress_changed,
                        'is_final_contract': is_final_contract,
                        'estimate_number': crawled_row[10] if len(crawled_row) > 10 else ""
                    })
                else:
                    # [DEEP CHECK] 기본 정보 변경이 없을 때, 숨겨진 '견적 내용' 변경 확인
                    sheet_row = existing_item['data']
                    estimate_count = sheet_row[5].strip() if len(sheet_row) > 5 else "0건"
                    progress = sheet_row[8].strip() if len(sheet_row) > 8 else ""

                    # 조건: 견적서 1건 이상, 최종계약체결/신청종료 아님
                    if estimate_count != "0건" and progress not in ["최종계약체결", "신청종료"]:
                        estimate_number = crawled_row[10] if len(crawled_row) > 10 else ""
                        if estimate_number:
                            print(f"[DEEP CHECK] 행 {existing_item['row_index']} 견적 상세 정보 확인 중...")
                            
                            # 현재 웹의 견적 상세 정보 크롤링
                            current_details = get_estimate_details_by_number(driver, estimate_number)
                            
                            # 시트의 기존 견적 상세 정보
                            old_details = sheet_row[9].strip() if len(sheet_row) > 9 else ""
                            
                            if current_details and current_details != "없음" and current_details != old_details:
                                print(f"[DEEP CHECK] 견적 내용 변경 감지! 행 {existing_item['row_index']}")
                                
                                # 시트 J열 업데이트
                                update_estimate_details(sheet, existing_item['row_index'], current_details)
                                
                                # 변경 사항 목록에 추가
                                changed_rows.append({
                                    'row_index': existing_item['row_index'],
                                    'crawled_data': crawled_row,
                                    'changes': [f"견적 상세 변경: '{old_details}' -> '{current_details}'"],
                                    'changed_cols': ["견적서제출현황"],
                                    'estimate_details_changed': True, # 숨겨진 변경 플래그
                                    'estimate_number': estimate_number
                                })
            else:
                # 완전 신규 항목 (번호-게임사 기준)
                print(f"신규 항목 발견: 번호 {key[0]} - 게임사 {key[1]}")
                new_rows.append(crawled_row)
        
        print(f"\n===== 분석 결과 =====")
        print(f"신규 항목: {len(new_rows)}개")
        print(f"변경 항목: {len(changed_rows)}개")
        
        # 신규 항목 추가
        if new_rows:
            print("\n신규 항목 추가 중...")
            print(f"시트명 확인: {sheet.title}")
            print(f"워크시트명 확인: {sheet.worksheet.title if hasattr(sheet, 'worksheet') else 'N/A'}")
            
            for i, row in enumerate(new_rows, 1):
                try:
                    # 특수 문자 처리
                    sanitized_row = [sanitize_text(cell) for cell in row]
                    
                    # 행 길이 맞추기
                    original_len = len(sanitized_row)
                    if len(sanitized_row) < header_len:
                        sanitized_row = sanitized_row + [''] * (header_len - len(sanitized_row))
                    elif len(sanitized_row) > header_len:
                        sanitized_row = sanitized_row[:header_len]
                    
                    print(f"신규 항목 {i}/{len(new_rows)} 추가 중... (원본길이: {original_len}, 조정후: {len(sanitized_row)})")
                    print(f"  - 번호: {sanitized_row[0]}, 서비스요청명: {sanitized_row[3]}, 게임사: {sanitized_row[4]}")
                    
                    # 구글 시트에 행 추가
                    result = sheet.append_row(sanitized_row)
                    print(f"  [OK] 추가 성공: {result}")
                    
                    time.sleep(1)  # API 제한 방지
                    
                except Exception as e:
                    print(f"  [ERROR] 신규 항목 {i} 추가 실패: {e}")
                    print(f"  - 실패한 행 데이터: {row[:5] if len(row) >= 5 else row}")
                    continue
        
        # 변경 항목 업데이트
        updated_rows = []
        if changed_rows:
            print("\n변경 항목 업데이트 중...")
            for item in changed_rows:
                row_index = item['row_index']
                crawled_data = item['crawled_data']
                
                # 기본 데이터 업데이트 (0-8번째 컬럼)
                base_data = crawled_data[:9]
                if len(base_data) < 9:
                    base_data = base_data + [''] * (9 - len(base_data))
                
                # 견적서 제출 건수 변경이고 0건이 아닌 경우 상세 정보 업데이트 필요
                need_estimate_detail = (
                    item['estimate_count_changed'] and 
                    len(crawled_data) > 5 and 
                    crawled_data[5].strip() != "0건"
                )
                
                if need_estimate_detail:
                    print(f"견적서 상세 정보 업데이트 필요: {crawled_data[0]}")
                    # 이 부분은 나중에 main에서 처리
                
                # A열부터 I열까지 업데이트 (0-8번째)
                update_range = f'A{row_index}:I{row_index}'
                sheet.update(values=[base_data], range_name=update_range)
                
                # 견적서 넘버는 페이지 이동용으로만 사용, 구글 시트에는 저장하지 않음
                # K열은 최종계약체결 시에만 계약협력사명으로 업데이트됨
                
                updated_rows.append(item)
                time.sleep(2)  # API 제한 방지
        
        print(f"\n===== 업데이트 완료 =====")
        print(f"신규 추가: {len(new_rows)}건")
        print(f"변경 업데이트: {len(updated_rows)}건")
        
        return new_rows, updated_rows
        
    except Exception as e:
        print(f"최적화된 업데이트 중 오류 발생: {e}")
        return [], []

def add_all_new_data(sheet, crawled_data):
    """
    구글 시트가 비어있을 때 모든 데이터를 신규 추가
    """
    # 헤더 행을 가져와서 정확한 컬럼 수 확인
    header = sheet.row_values(1)
    header_len = len(header)
    print(f"헤더 컬럼 수: {header_len}")
    
    new_rows = []
    for i, row in enumerate(crawled_data, 1):
        try:
            # 특수 문자 처리
            sanitized_row = [sanitize_text(cell) for cell in row]
            
            # 행 길이를 헤더 길이에 맞추기
            original_len = len(sanitized_row)
            if len(sanitized_row) < header_len:
                sanitized_row = sanitized_row + [''] * (header_len - len(sanitized_row))
            elif len(sanitized_row) > header_len:
                sanitized_row = sanitized_row[:header_len]
            
            print(f"신규 항목 {i}/{len(crawled_data)} 추가 중... (원본길이: {original_len}, 조정후: {len(sanitized_row)})")
            print(f"  - 번호: {sanitized_row[0]}, 서비스요청명: {sanitized_row[3] if len(sanitized_row) > 3 else 'N/A'}, 게임사: {sanitized_row[4] if len(sanitized_row) > 4 else 'N/A'}")
            
            # 구글 시트에 행 추가
            result = sheet.append_row(sanitized_row)
            print(f"  [OK] 추가 성공")
            
            new_rows.append(sanitized_row)
            time.sleep(1)  # API 제한 방지
            
        except Exception as e:
            print(f"  [ERROR] 신규 항목 {i} 추가 실패: {e}")
            print(f"  - 실패한 행 데이터: {row[:5] if len(row) >= 5 else row}")
            continue
    
    return new_rows, []

def get_estimate_details_by_number(driver, estimate_number):
    """
    견적서 넘버를 사용해서 상세 페이지에서 견적 정보 추출
    """
    try:
        # JavaScript로 상세 페이지 호출
        driver.execute_script(f"serviceReqEstimateListPage('{estimate_number}')")
        
        # 상세페이지 테이블 로딩 대기
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.division30 #dataList"))
        )
        time.sleep(1)
        
        # 견적 정보 추출 (기존 방식과 동일)
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
        
    except Exception as e:
        print(f"견적서 상세 정보 추출 실패: {e}")
        return "없음"

def get_contract_details_by_number(driver, estimate_number):
    """
    최종계약체결시 계약 상세 정보 추출
    """
    try:
        # JavaScript로 상세 페이지 호출
        driver.execute_script(f"serviceReqEstimateListPage('{estimate_number}')")
        
        # 상세페이지 테이블 로딩 대기
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.division30 #dataList"))
        )
        time.sleep(1)
        
        # 계약 정보 추출
        detail_rows = driver.find_elements(By.CSS_SELECTOR, "div.division30 #dataList tbody tr")
        
        # "최종계약체결" 상태인 협력사 찾기
        selected_company = ""
        contract_amount = ""
        start_date = ""
        end_date = ""
        
        for row in detail_rows:
            dtds = row.find_elements(By.TAG_NAME, "td")
            
            if len(dtds) >= 11:  # 11번째 컬럼(진행상황)까지 있는지 확인
                try:
                    # 11번째 컬럼(진행상황) 확인
                    progress_cell = dtds[10]  # 0부터 시작하므로 11번째는 인덱스 10
                    a_tag = progress_cell.find_element(By.TAG_NAME, "a")
                    
                    if a_tag.text.strip() == "최종계약체결":
                        # 이 행이 선정된 협력사!
                        print(f"최종계약체결 협력사 발견: {dtds[2].text.strip()}")
                        
                        selected_company = dtds[2].text.strip()  # 협력사
                        contract_amount = dtds[5].text.strip()   # 견적금액 (계약금액으로 사용)
                        
                        # 계약기간 (과업기간) - 8번째 항목
                        contract_period = dtds[7].text.strip()
                        if ' ~ ' in contract_period:
                            start_date, end_date = contract_period.split(' ~ ')
                            start_date = start_date.strip()
                            end_date = end_date.strip()
                        
                        break  # 찾았으므로 루프 종료
                        
                except Exception as e:
                    # a태그가 없거나 다른 형태인 경우 건너뜀
                    continue
        
        # 원래 페이지로 복귀
        driver.back()
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "dataList"))
        )
        time.sleep(1)
        
        return {
            'company': selected_company,
            'amount': contract_amount,
            'start_date': start_date,
            'end_date': end_date
        }
        
    except Exception as e:
        print(f"계약 상세 정보 추출 실패: {e}")
        return None

def update_estimate_details(sheet, row_index, estimate_details):
    """
    J열(9번째 컬럼)에 견적서 상세 정보 업데이트
    """
    try:
        sheet.update(values=[[estimate_details]], range_name=f'J{row_index}')
        print(f"견적서 상세 정보 업데이트 완료: 행 {row_index}")
        time.sleep(1)
    except Exception as e:
        print(f"견적서 상세 정보 업데이트 실패: {e}")

def update_contract_details(sheet, row_index, contract_details):
    """
    K열(계약협력사), L열(계약금액), M열(업무시작일), N열(업무종료일) 업데이트
    """
    try:
        # K열: 계약협력사
        if contract_details['company']:
            sheet.update(values=[[contract_details['company']]], range_name=f'K{row_index}')
            print(f"계약협력사 업데이트 완료: 행 {row_index}")
        
        # L열: 계약금액  
        if contract_details['amount']:
            sheet.update(values=[[contract_details['amount']]], range_name=f'L{row_index}')
            print(f"계약금액 업데이트 완료: 행 {row_index}")
        
        # M열: 업무시작일
        if contract_details['start_date']:
            sheet.update(values=[[contract_details['start_date']]], range_name=f'M{row_index}')
            print(f"업무시작일 업데이트 완료: 행 {row_index}")
        
        # N열: 업무종료일
        if contract_details['end_date']:
            sheet.update(values=[[contract_details['end_date']]], range_name=f'N{row_index}')
            print(f"업무종료일 업데이트 완료: 행 {row_index}")
            
        time.sleep(2)  # API 제한 방지
        
    except Exception as e:
        print(f"계약 상세 정보 업데이트 실패: {e}") 

def process_contract_changes(contract_changes, sheet):
    """
    계약변경관리 페이지에서 크롤링한 데이터를 처리하는 함수
    
    Args:
        contract_changes: 계약변경관리 페이지에서 크롤링한 데이터 목록
        sheet: 구글 시트 객체
    
    Returns:
        updated_contracts: 업데이트된 계약 목록 (알림용)
    """
    print("\n[CONTRACT_CHANGE] 계약변경 데이터 처리 시작")
    print(f"[CONTRACT_CHANGE] 총 {len(contract_changes)}개 항목 처리 예정")
    
    # 구글 시트에서 모든 데이터 가져오기
    all_sheet_data = sheet.get_all_values()
    header = all_sheet_data[0]  # 헤더 행
    sheet_data = all_sheet_data[1:]  # 데이터 행 (헤더 제외)
    
    # 업데이트된 계약 목록 (알림용)
    updated_contracts = []
    
    # 각 계약변경 항목 처리
    for change_item in contract_changes:
        try:
            # 필요한 데이터 추출
            # 상세 서비스 부문(3), 서비스 요청명(4), 협력사(5), 게임사(6), 포인트(7), 계약기간(8), 진행상황(11)
            service_detail = change_item[3] if len(change_item) > 3 else ""
            service_req_name = change_item[4] if len(change_item) > 4 else ""
            company = change_item[5] if len(change_item) > 5 else ""
            game_company = change_item[6] if len(change_item) > 6 else ""
            points = change_item[7] if len(change_item) > 7 else ""
            contract_period = change_item[8] if len(change_item) > 8 else ""
            progress_status = change_item[11] if len(change_item) > 11 else ""
            
            # 진행상황이 "계약변경 신청"인 경우 처리하지 않음
            if progress_status == "계약변경 신청":
                print(f"[CONTRACT_CHANGE] 계약변경 신청 상태 항목 건너뜀: {service_req_name} ({game_company})")
                continue
            
            # 진행상황이 "계약변경 승인(게임사)" 또는 "계약변경 완료"인 경우만 처리
            if progress_status not in ["계약변경 승인(게임사)", "계약변경 완료"]:
                print(f"[CONTRACT_CHANGE] 처리 대상 아님: {service_req_name} ({game_company}) - {progress_status}")
                continue
            
            # 계약기간 분리 (예: "2025-06-23 ~ 2025-07-18" -> "2025-06-23", "2025-07-18")
            start_date = ""
            end_date = ""
            if contract_period and " ~ " in contract_period:
                dates = contract_period.split(" ~ ")
                if len(dates) == 2:
                    start_date = dates[0].strip()
                    end_date = dates[1].strip()
            
            # 구글 시트에서 일치하는 항목 찾기
            found = False
            for i, row in enumerate(sheet_data):
                # 식별자 비교: 상세 서비스 부문(C열), 서비스 요청명(D열), 협력사(K열), 게임사(E열)
                if (len(row) > 2 and row[2] == service_detail and 
                    len(row) > 3 and row[3] == service_req_name and 
                    len(row) > 10 and row[10] == company and 
                    len(row) > 4 and row[4] == game_company):
                    
                    found = True
                    row_index = i + 2  # 헤더(1) + 인덱스(0부터 시작)
                    
                    # 변경 사항 기록
                    changes = []
                    
                    # 기존 값 가져오기
                    old_points = row[11] if len(row) > 11 else ""
                    old_start_date = row[12] if len(row) > 12 else ""
                    old_end_date = row[13] if len(row) > 13 else ""
                    
                    # 변경 사항 확인
                    if points and points != old_points:
                        changes.append(f"계약금액: {old_points} → {points}")
                    
                    if start_date and start_date != old_start_date:
                        changes.append(f"업무시작일: {old_start_date} → {start_date}")
                    
                    if end_date and end_date != old_end_date:
                        changes.append(f"업무종료일: {old_end_date} → {end_date}")
                    
                    # 변경 사항이 있는 경우에만 업데이트 및 알림
                    if changes:
                        # 계약금액(L열) 업데이트
                        if points and points != old_points:
                            sheet.update(values=[[points]], range_name=f'L{row_index}')
                            print(f"[CONTRACT_CHANGE] 계약금액 업데이트: {old_points} → {points}")
                        
                        # 업무시작일(M열) 업데이트
                        if start_date and start_date != old_start_date:
                            sheet.update(values=[[start_date]], range_name=f'M{row_index}')
                            print(f"[CONTRACT_CHANGE] 업무시작일 업데이트: {old_start_date} → {start_date}")
                        
                        # 업무종료일(N열) 업데이트
                        if end_date and end_date != old_end_date:
                            sheet.update(values=[[end_date]], range_name=f'N{row_index}')
                            print(f"[CONTRACT_CHANGE] 업무종료일 업데이트: {old_end_date} → {end_date}")
                        
                        # 알림 목록에 추가 (한 번만)
                        updated_contracts.append({
                            'service_name': service_req_name,
                            'game_company': game_company,
                            'company': company,
                            'changes': changes,
                            'row_index': row_index,
                            'progress_status': progress_status
                        })
                        print(f"[CONTRACT_CHANGE] 변경사항 감지: {service_req_name} ({game_company}) - {len(changes)}개 필드 변경")
                    else:
                        print(f"[CONTRACT_CHANGE] 변경사항 없음: {service_req_name} ({game_company})")
                    
                    # API 제한 방지
                    time.sleep(1)
                    break
            
            if not found:
                print(f"[CONTRACT_CHANGE] 일치하는 계약 정보를 찾을 수 없음: {service_req_name} ({game_company})")
        
        except Exception as e:
            print(f"[CONTRACT_CHANGE] 계약변경 처리 중 오류: {e}")
            continue
    
    print(f"[CONTRACT_CHANGE] 계약변경 데이터 처리 완료: {len(updated_contracts)}개 항목 업데이트")
    return updated_contracts

def send_contract_change_notifications(updated_contracts):
    """
    계약변경 알림 발송 함수
    
    Args:
        updated_contracts: 업데이트된 계약 목록
    """
    if not updated_contracts:
        print("[CONTRACT_CHANGE] 알림 대상 없음")
        return
    
    print(f"[CONTRACT_CHANGE] 알림 발송 시작: {len(updated_contracts)}개 항목")
    
    # 담당자 정보 가져오기
    contact_map = get_contact_map()
    
    # 알림 발송 통계
    email_sent = 0
    telegram_sent = 0
    
    for contract in updated_contracts:
        try:
            service_req_name = contract['service_name']  # 변수명은 그대로 두고 내부적으로 service_req_name으로 처리
            game_company = contract['game_company']
            company = contract['company']
            changes = contract['changes']
            progress_status = contract['progress_status']
            
            # 담당자 정보 확인
            contact_info = contact_map.get(game_company)
            
            # 담당자가 있는 경우에만 알림 발송
            if contact_info:
                # 특수 문자 처리
                sanitized_service_req_name = sanitize_text(service_req_name)
                sanitized_game_company = sanitize_text(game_company)
                sanitized_company = sanitize_text(company)
                sanitized_progress = sanitize_text(progress_status)
                
                # 변경 내용 텍스트 구성
                changes_text = '\n'.join(changes)
                sanitized_changes = sanitize_text(changes_text)
                
                # 알림 메시지 구성
                message = f"""🔄 [계약변경] {sanitized_game_company} - {sanitized_service_req_name}

협력사: {sanitized_company}
진행상황: {sanitized_progress}

변경 내용:
{sanitized_changes}

계약변경관리 페이지에서 변경 사항이 감지되어 자동으로 업데이트되었습니다."""
                
                # 텔레그램 알림 발송
                from notification import send_notification
                send_notification(message)
                telegram_sent += 1
                print(f"[CONTRACT_CHANGE] 텔레그램 알림 발송 완료: {game_company} - {service_req_name}")
                
                # 이메일 발송
                email_title = f"[게임더하기] {sanitized_game_company} - 계약변경 알림"
                email_body = f"""
{contact_info['name']}님, 안녕하세요.
게임더하기 DRIC_BOT입니다.

[{sanitized_service_req_name}] 계약 정보에 변경 사항이 있어 알려드립니다.
게임사: {sanitized_game_company}
협력사: {sanitized_company}

변경 내용:
{sanitized_changes}

계약변경관리 페이지에서 변경 사항이 감지되어 자동으로 업데이트되었습니다.
확인 부탁드립니다.

감사합니다.
"""
                
                # 이메일 발송 함수 호출
                try:
                    import yagmail
                    import os
                    
                    EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
                    EMAIL_APP_PASSWORD = os.environ.get('EMAIL_APP_PASSWORD')
                    
                    if EMAIL_SENDER and EMAIL_APP_PASSWORD:
                        yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_APP_PASSWORD)
                        yag.send(
                            to=contact_info['email'],
                            subject=email_title,
                            contents=email_body
                        )
                        email_sent += 1
                        print(f"[CONTRACT_CHANGE] 이메일 알림 발송 완료: {contact_info['name']}({contact_info['email']})")
                    else:
                        print("[CONTRACT_CHANGE] 이메일 환경변수가 설정되지 않았습니다.")
                        
                except Exception as e:
                    print(f"[CONTRACT_CHANGE] 이메일 발송 실패: {e}")
            else:
                print(f"[CONTRACT_CHANGE] 담당자 정보 없음: {game_company} - {service_req_name} (알림 발송 건너뜀)")
            
        except Exception as e:
            print(f"[CONTRACT_CHANGE] 알림 발송 중 오류: {e}")
            continue
    
    print(f"[CONTRACT_CHANGE] 알림 발송 완료: 이메일 {email_sent}건, 텔레그램 {telegram_sent}건") 