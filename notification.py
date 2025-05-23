import yagmail
import os
import requests

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