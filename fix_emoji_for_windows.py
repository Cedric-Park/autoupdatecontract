#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 환경 이모지 호환성 수정 스크립트
모든 Python 파일의 이모지를 Windows 호환 텍스트로 변경
"""

import os
import re

# 이모지 → 텍스트 매핑
EMOJI_MAP = {
    '🚀': '[START]',
    '🔍': '[CRAWL]', 
    '✅': '[OK]',
    '❌': '[ERROR]',
    '📱': '[TELEGRAM]',
    '🔔': '[ALERT]',
    '📋': '[ESTIMATE]',
    '📧': '[EMAIL]',
    '🏆': '[CONTRACT]',
    '📄': '[INFO]',
    '🏁': '[END]',
    '🔄': '[UPDATE]',
    '📈': '[RESULT]',
    '🆕': '[NEW]',
    '📝': '[DETAIL]',
    '🎯': '[TOTAL]',
    '⏰': '[WAIT]',
    '💡': '[TIP]',
    '🧪': '[TEST]',
    '📍': '[PATH]',
    '⚠️': '[WARNING]',
    '🎮': '[GAME]',
    '💾': '[SAVE]',
    '🟢': '[ON]',
    '🔴': '[OFF]',
    '▶️': '[PLAY]',
    '⏹️': '[STOP]',
    '⚙️': '[CONFIG]'
}

def fix_emoji_in_file(file_path):
    """파일의 이모지를 텍스트로 변경"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # 이모지 교체
        for emoji, text in EMOJI_MAP.items():
            if emoji in content:
                content = content.replace(emoji, text)
                changes_made += content.count(text) - original_content.count(text)
        
        # 변경사항이 있으면 파일 저장
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] {file_path}: {changes_made}개 이모지 변경")
            return True
        else:
            print(f"[SKIP] {file_path}: 변경할 이모지 없음")
            return False
            
    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")
        return False

def main():
    print("[START] Windows 이모지 호환성 수정 시작")
    print("=" * 50)
    
    # 현재 디렉토리의 모든 Python 파일 찾기
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and not file.startswith('fix_emoji'):
                python_files.append(os.path.join(root, file))
    
    if not python_files:
        print("[ERROR] Python 파일을 찾을 수 없습니다.")
        return
    
    print(f"[INFO] 발견된 Python 파일: {len(python_files)}개")
    print("-" * 50)
    
    # 각 파일 처리
    fixed_files = 0
    for file_path in python_files:
        if fix_emoji_in_file(file_path):
            fixed_files += 1
    
    print("-" * 50)
    print(f"[RESULT] 수정 완료: {fixed_files}/{len(python_files)}개 파일")
    print("[END] Windows 이모지 호환성 수정 완료")

if __name__ == "__main__":
    main() 