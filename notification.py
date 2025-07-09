import yagmail
import os
import requests
import re

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

def make_change_alert(row, changes, changed_cols, contact_info=None, estimate_details=None):
    """
    변경 알림 메시지 생성 함수
    이메일용과 텔레그램용 메시지를 다르게 생성하고, 숨겨진 변경 유형에 대한 처리 추가
    """
    company = row[4]
    service_req = row[3]
    col_str = ', '.join(changed_cols)
    
    # 특수 문자 처리
    sanitized_company = sanitize_text(company)
    sanitized_service_req = sanitize_text(service_req)
    sanitized_deadline_date = sanitize_text(row[6]) if len(row) > 6 else ""
    sanitized_selection_date = sanitize_text(row[7]) if len(row) > 7 else ""
    sanitized_progress_status = sanitize_text(row[8]) if len(row) > 8 else ""
    
    # 숨겨진 '견적 상세 변경'인지 확인
    is_hidden_change = 'estimate_details_changed' in changes and changes['estimate_details_changed']

    # 담당자 정보 처리
    if contact_info:
        to_name = contact_info['name']
        greeting = f"안녕하세요, {to_name}님."
        telegram_greeting = f"{to_name}님, 게임사"
    else:
        to_name = "담당자"
        greeting = f"안녕하세요."
        telegram_greeting = f"[WARNING] 담당자 미등록 | 게임사"
    
    # 기본 계약 정보 (현재 값 기준)
    deadline_date = row[6]  # 입찰 마감일
    selection_date = row[7]  # 선정 마감일
    progress_status = row[8]  # 진행상황
    
    # 변경 항목 포맷팅 (견적서 제출현황은 특별 처리)
    formatted_changes = []
    estimate_changes = None
    
    # 변경 항목 특수 문자 처리
    sanitized_changes = []
    for change_str in changes:
        sanitized_changes.append(sanitize_text(change_str))
    
    for change_str in sanitized_changes:
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
    if is_hidden_change:
        email_title = f"[게임더하기] {sanitized_company} - 견적 내용 변경 알림 (금액 등)"
    else:
        email_title = f"[게임더하기] {sanitized_company} - 계약 정보 변경 알림 [{col_str}]"
    
    # 본문 구성
    email_body = f"""
{greeting}
게임더하기 DRIC_BOT입니다.

[{sanitized_service_req}] 계약 정보에 변경 사항이 있어 알려드립니다.
게임사: {sanitized_company}

계약 기본 정보:
- 입찰 마감일: {sanitized_deadline_date}
- 진행상황: {sanitized_progress_status}

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
    
    # J열에서 가져온 최신 견적서 상세 정보 추가
    if estimate_details:
        sanitized_estimate_details = sanitize_text(estimate_details)
        formatted_estimate = format_estimate_details(sanitized_estimate_details)
        email_body += f"""[ESTIMATE] 제출된 견적서 상세 내용:
{formatted_estimate}

"""
    
    email_body += """확인 부탁드립니다.
감사합니다."""
    
    # 텔레그램용 메시지 (더 간결하게)
    if is_hidden_change:
        telegram_title = f"🔔 [{sanitized_company}] 견적 내용 변경"
    else:
        telegram_title = f"🚨 [{sanitized_company}] 계약 정보 변경"
        
    telegram_body = f"""
{telegram_greeting} [{sanitized_company}]의 '{sanitized_service_req}' 계약 정보가 변경되었습니다.

📅 입찰 마감일: {sanitized_deadline_date}
🔄 진행상황: {sanitized_progress_status}
"""
    
    # 변경 항목이 있는 경우 추가
    if formatted_changes:
        telegram_body += "\n변경된 항목:\n" + "\n".join(formatted_changes) + "\n"
    
    # 견적서 변경 정보가 있는 경우 별도 섹션으로 추가
    if estimate_changes:
        # 숨겨진 변경의 경우, 변경 전/후를 더 명확하게 보여줌
        if is_hidden_change:
            telegram_body += "\n📋 견적 내용 변경:\n" + "\n".join(sanitized_changes)
        else:
            telegram_body += f"""
📋 견적서 제출 현황:
- 변경 전: {estimate_changes['old']}
- 변경 후:
{estimate_changes['new']}
"""
    
    # J열에서 가져온 최신 견적서 상세 정보 추가
    if estimate_details:
        sanitized_estimate_details = sanitize_text(estimate_details)
        formatted_estimate = format_estimate_details(sanitized_estimate_details)
        telegram_body += f"""
📋 제출된 견적서 상세 내용:
{formatted_estimate}
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
    
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
    EMAIL_APP_PASSWORD = os.environ.get('EMAIL_APP_PASSWORD')
    
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
        
        # 특수 문자 처리
        sanitized_company = sanitize_text(company)
        sanitized_service_name = sanitize_text(row[3]) if len(row) > 3 else ""
        sanitized_service_type = sanitize_text(row[1]) if len(row) > 1 else ""
        sanitized_deadline = sanitize_text(row[6]) if len(row) > 6 else ""
        sanitized_estimate = sanitize_text(row[5]) if len(row) > 5 else ""
        sanitized_progress = sanitize_text(row[8]) if len(row) > 8 else ""
        
        subject = f"[게임더하기] {sanitized_company} 신규 계약 [{sanitized_service_name}] 업데이트 알림"
        body = f"""
{to_name}님, 안녕하세요.
게임더하기 DRIC_BOT입니다.

게임사 [{sanitized_company}]에서 신규 계약(서비스 부문: {sanitized_service_type})이 업데이트 되었습니다.\n\n- 서비스 요청명: {sanitized_service_name}\n- 입찰 마감일: {sanitized_deadline}\n- 제출된 견적서 : {sanitized_estimate}\n- 진행상황: {sanitized_progress}\n
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
    
    # 특수 문자 처리
    sanitized_message = sanitize_text(message)
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": sanitized_message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("텔레그램 알림 전송 완료")
    else:
        print("텔레그램 알림 실패:", response.text)

def generate_email_subject_from_message(message):
    """
    메시지 내용을 분석해서 적절한 이메일 제목 생성
    """
    # 줄 단위로 분리
    lines = message.strip().split('\n')
    first_line = lines[0] if lines else message
    
    # 개별 신규 계약 알림
    if "신규 계약 업데이트" in first_line:
        # "🔔 [넥셀론] 신규 계약 업데이트" 형식에서 게임사명 추출
        match = re.search(r'\[([^\]]+)\]', first_line)
        if match:
            company_name = match.group(1)
            return f"[게임더하기] {company_name} - 신규 계약 업데이트 알림"
        return "[게임더하기] 신규 계약 업데이트 알림"
    
    # 개별 게임사 변경사항 알림
    elif "계약 정보 변경" in first_line:
        # "🚨 [넥셀론] 계약 정보 변경" 형식에서 게임사명 추출
        match = re.search(r'\[([^\]]+)\]', first_line)
        if match:
            company_name = match.group(1)
            return f"[게임더하기] {company_name} - 계약 정보 변경 알림"
        return "[게임더하기] 계약 정보 변경 알림"
    
    # 오류 알림
    elif "[ERROR]" in first_line or "오류" in first_line:
        return "[게임더하기] 시스템 오류 알림"
    
    # 기타 알림
    else:
        return "[게임더하기] 시스템 알림"

def send_notification(message):
    """
    통합 알림 함수: 텔레그램으로 알림 발송
    """
    try:
        # 텔레그램 알림
        send_telegram_message(message)
        print("[TELEGRAM] 텔레그램 알림 발송 완료")
            
    except Exception as e:
        print(f"[ERROR] 알림 발송 실패: {e}") 