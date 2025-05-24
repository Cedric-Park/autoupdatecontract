from notification import generate_email_subject_from_message

# 테스트 케이스들
test_cases = [
    "[NEW] 신규 계약 등록 알림\n\n총 3건의 신규 계약이 등록되었습니다.",
    "[ALERT] [넥셀론] 신규 계약 업데이트\n\n박종철님, 게임사 [넥셀론]에서 신규 계약이 등록되었습니다.",
    "[ALERT] [컴투스] 계약 정보 변경\n\n담당자님, 게임사 [컴투스]의 계약 정보가 변경되었습니다.",
    "[ERROR] 프로그램 실행 중 오류 발생: 크롤링 실패",
    "일반적인 시스템 메시지"
]

print("=== 이메일 제목 생성 테스트 ===")
for i, test_msg in enumerate(test_cases, 1):
    subject = generate_email_subject_from_message(test_msg)
    print(f"테스트 {i}: {subject}")
    print(f"  원본: {test_msg.split(chr(10))[0]}")  # 첫 번째 줄만 표시
    print() 