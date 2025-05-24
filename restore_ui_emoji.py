#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 이모지 복원 스크립트
dashboard.py의 UI 요소에만 이모지를 복원하고, print문은 그대로 둠
"""

import re

def restore_ui_emoji():
    """dashboard.py의 UI 요소만 이모지 복원"""
    
    # UI 이모지 매핑 (UI 요소에만 사용)
    UI_EMOJI_MAP = {
        '[GAME]': '🎮',
        '[PLAY]': '▶️', 
        '[STOP]': '⏹️',
        '[START]': '🚀',
        '[SAVE]': '💾',
        '[CONFIG]': '⚙️',
        '[ON]': '🟢',
        '[OFF]': '🔴',
        '[INFO]': '📄'
    }
    
    try:
        with open('dashboard.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # UI 텍스트만 선별적으로 이모지 복원
        ui_patterns = [
            # 제목
            r'text="(\[GAME\] 게임더하기 계약 관리 자동화 대시보드)"',
            # 버튼 텍스트
            r'text="(\[PLAY\] 자동 실행 시작)"',
            r'text="(\[STOP\] 자동 실행 중지)"', 
            r'text="(\[START\] 즉시 실행)"',
            r'text="(\[SAVE\] 설정 저장)"',
            # 라벨프레임 텍스트
            r'text="(\[CONFIG\] 설정)"',
            # 상태 표시
            r'text="(\[ON\] 자동 실행 중)"',
            r'text="(\[OFF\] 중지됨)"',
            # 로그 메시지에서 UI 관련 부분만
            r'self\.add_log\("(\[START\] 대시보드가 시작되었습니다\.)"',
            r'self\.add_log\("(\[SAVE\] 설정이 저장되었습니다\.)"'
        ]
        
        # 패턴별로 이모지 복원
        for pattern in ui_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                for text_key, emoji in UI_EMOJI_MAP.items():
                    if text_key in match:
                        new_text = match.replace(text_key, emoji)
                        content = content.replace(f'"{match}"', f'"{new_text}"')
        
        # 변경사항이 있으면 저장
        if content != original_content:
            with open('dashboard.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print("[OK] dashboard.py UI 이모지 복원 완료")
            return True
        else:
            print("[INFO] 복원할 UI 이모지 없음")
            return False
            
    except Exception as e:
        print(f"[ERROR] UI 이모지 복원 실패: {e}")
        return False

if __name__ == "__main__":
    print("[START] UI 이모지 복원 시작")
    restore_ui_emoji()
    print("[END] UI 이모지 복원 완료") 