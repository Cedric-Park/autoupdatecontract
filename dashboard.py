import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import os
import re
import sys

class ModernStyle:
    """모던 스타일 설정"""
    def __init__(self):
        # 깔끔한 모던 다크 테마 색상 팔레트 (파스텔톤)
        self.colors = {
            'bg_primary': '#222428',      # 메인 배경 (새로운 색상)
            'bg_secondary': '#15191E',    # 카드 배경 (새로운 색상)
            'bg_tertiary': '#0f0f0f',     # 입력 필드 배경 (메인 배경과 동일)
            'title_bg': '#222428',        # 타이틀 영역 배경 (새로운 색상)
            'accent_blue': '#87CEEB',     # 파스텔 블루 (스카이블루)
            'accent_green': '#98D8C8',    # 파스텔 그린 (민트그린)  
            'accent_red': '#F8BBD9',      # 파스텔 핑크 (로즈)
            'accent_purple': '#D1C4E9',   # 파스텔 퍼플 (라벤더)
            'accent_orange': '#FFCC80',   # 파스텔 오렌지 (피치)
            'text_primary': '#ffffff',    # 흰색 텍스트
            'text_secondary': '#b0b0b0',  # 밝은 회색 텍스트
            'text_muted': '#808080',      # 중간 회색 텍스트
            'border': '#15191E',          # 테두리를 카드 배경색과 같게
            'shadow': '#000000',          # 그림자
        }
    
    def configure_ttk_style(self):
        """ttk 스타일 설정"""
        style = ttk.Style()
        
        # 전체 테마 설정
        style.theme_use('clam')
        
        # Label 스타일 - 더 깔끔하게
        style.configure('Title.TLabel', 
                       background=self.colors['title_bg'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 28, 'bold'))
        
        style.configure('Subtitle.TLabel',
                       background=self.colors['title_bg'],
                       foreground=self.colors['accent_blue'],
                       font=('Segoe UI', 14))
        
        style.configure('Header.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 11, 'bold'))
        
        style.configure('Body.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_secondary'],
                       font=('Segoe UI', 10))
        
        style.configure('Success.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['accent_green'],
                       font=('Segoe UI', 12, 'bold'))
        
        style.configure('Error.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['accent_red'],
                       font=('Segoe UI', 12, 'bold'))
        
        style.configure('Running.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['accent_orange'],
                       font=('Segoe UI', 12, 'bold'))
        
        # Frame 스타일 - 더 깔끔한 카드
        style.configure('TLabelFrame',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       font=('Segoe UI', 11, 'bold'))
        
        style.configure('TLabelFrame.Label',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 11, 'bold'))
        
        style.configure('TFrame',
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        # Button 스타일 - 모던하고 깔끔하게 (파스텔 + 작은 크기)
        style.configure('Primary.TButton',
                       background='#4677A7',    # 블루로 변경
                       foreground='#FFFFFF',    # 흰색 텍스트로 변경
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))  # 패딩 줄임
        
        style.map('Primary.TButton',
                  background=[('active', '#5B8BC7'), ('pressed', '#3A5F8A')])  # 호버/클릭 시 색상도 조정
        
        style.configure('Success.TButton',
                       background='#3B9B60',    # 진한 녹색으로 변경
                       foreground='#FFFFFF',    # 흰색 텍스트로 변경
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))  # 패딩 줄임
        
        style.map('Success.TButton',
                  background=[('active', '#4CAF70'), ('pressed', '#2E7D50')])  # 호버/클릭 시 색상도 조정
        
        style.configure('Danger.TButton',
                       background='#DD5D5C',    # 빨간색으로 변경
                       foreground='#FFFFFF',    # 흰색 텍스트로 변경
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))  # 패딩 줄임
        
        style.map('Danger.TButton',
                  background=[('active', '#E77B7B'), ('pressed', '#B94A4A')])  # 호버/클릭 시 색상도 조정
        
        style.configure('Warning.TButton',
                       background='#5C45A2',    # 보라색으로 변경
                       foreground='#FFFFFF',    # 흰색 텍스트로 변경
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))  # 패딩 줄임
        
        style.map('Warning.TButton',
                  background=[('active', '#7B5FBF'), ('pressed', '#4A3485')])  # 호버/클릭 시 색상도 조정
        
        # Combobox 스타일 - 더 깔끔하게
        style.configure('Modern.TCombobox',
                       fieldbackground=self.colors['bg_tertiary'],
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       lightcolor=self.colors['border'],        # 테두리 색상을 더 어둡게
                       darkcolor=self.colors['border'],         # 테두리 색상을 더 어둡게
                       font=('Segoe UI', 10))
        
        # 콤보박스 상태별 색상 매핑 (포커스 유무 관계없이 동일한 배경색)
        style.map('Modern.TCombobox',
                  fieldbackground=[('active', self.colors['bg_tertiary']),
                                  ('focus', self.colors['bg_tertiary']),
                                  ('!focus', self.colors['bg_tertiary']),
                                  ('readonly', self.colors['bg_tertiary'])],
                  background=[('active', self.colors['bg_tertiary']),
                             ('focus', self.colors['bg_tertiary']),
                             ('!focus', self.colors['bg_tertiary']),
                             ('readonly', self.colors['bg_tertiary'])],
                  foreground=[('active', self.colors['text_primary']),
                             ('focus', self.colors['text_primary']),
                             ('!focus', self.colors['text_primary']),
                             ('readonly', self.colors['text_primary'])])
        
        # Checkbutton 스타일
        style.configure('Modern.TCheckbutton',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_secondary'],
                       focuscolor=self.colors['accent_blue'],
                       font=('Segoe UI', 10))
        
        return style

class GameDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 게임더하기 계약 관리 자동화 대시보드")
        self.root.geometry("800x900")  # 창 크기 축소 (1000 -> 800)
        
        # 모던 스타일 적용
        self.style_manager = ModernStyle()
        self.style = self.style_manager.configure_ttk_style()
        
        # 루트 윈도우 색상 설정
        self.root.configure(bg=self.style_manager.colors['bg_primary'])
        
        # 스케줄러 초기화
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # 상태 변수들
        self.is_running = False
        self.last_execution = None
        self.next_execution = None
        
        # 애니메이션 관련 변수
        self.status_blink_count = 0
        self.toast_windows = []
        
        # 설정 로드
        self.config = self.load_config()
        
        # UI 생성
        self.create_widgets()
        
        # Windows 다크 모드 제목 표시줄 적용
        self.root.after(100, lambda: apply_dark_title_bar(self.root))
        
        # 버튼 상태 초기화
        self.update_buttons()
        
        # 상태 업데이트 시작
        self.update_status()
        
        # 환영 토스트 표시
        self.root.after(1000, lambda: self.show_toast("🎮 NEON 게이밍 대시보드에 오신 것을 환영합니다! ⚡", "success"))
    
    def load_config(self):
        """설정 파일 로드"""
        config_file = "dashboard_config.json"
        default_config = {
            "execution_interval": 60,
            "last_settings": {},
            "immediate_start": True
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default_config
        return default_config
    
    def save_config(self, config=None):
        """설정 파일 저장"""
        if config is None:
            config = self.config
        
        with open("dashboard_config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def create_widgets(self):
        """깔끔하고 모던한 UI 위젯 생성"""
        # 메인 프레임
        main_frame = tk.Frame(self.root, bg=self.style_manager.colors['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=30, pady=15)  # 상단 패딩 30 -> 15로 줄임
        
        # 타이틀 섹션
        title_frame = tk.Frame(main_frame, bg=self.style_manager.colors['title_bg'])
        title_frame.pack(fill='x', pady=(0, 15))  # 하단 패딩 30 -> 15로 줄임
        
        # 메인 타이틀
        title_label = tk.Label(title_frame, text="게임더하기 계약 관리", 
                              bg=self.style_manager.colors['title_bg'],
                              fg=self.style_manager.colors['text_primary'],
                              font=('Segoe UI', 28, 'bold'))
        title_label.pack(pady=(15, 8))  # 상단 패딩 20 -> 15로 줄임
        
        # 서브타이틀
        subtitle_label = tk.Label(title_frame, text="자동화 대시보드 v2.0 NEON EDITION", 
                                 bg=self.style_manager.colors['title_bg'],
                                 fg='#B482E2',  # 보라색으로 변경
                                 font=('Segoe UI', 14, 'bold'))  # 굵게 변경
        subtitle_label.pack(pady=(0, 15))  # 하단 패딩 20 -> 15로 줄임
        
        # 구분선
        separator_frame = tk.Frame(title_frame, height=1, bg=self.style_manager.colors['border'])
        separator_frame.pack(fill='x', padx=60, pady=(0, 5))  # 하단 패딩 10 -> 5로 줄임
        
        # === 통합 제어 카드 (좌우 분할) ===
        control_card = tk.Frame(main_frame, bg=self.style_manager.colors['bg_secondary'], 
                               relief='solid', borderwidth=1, highlightbackground=self.style_manager.colors['border'])
        control_card.pack(fill='x', pady=(0, 15))  # 하단 패딩 20 -> 15로 줄임
        
        # 카드 제목
        tk.Label(control_card, text="시스템 제어 및 설정", 
                bg=self.style_manager.colors['bg_secondary'],
                fg=self.style_manager.colors['text_primary'],
                font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=20, pady=(15, 10))
        
        # === 좌우 분할 컨테이너 ===
        main_container = tk.Frame(control_card, bg=self.style_manager.colors['bg_secondary'])
        main_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # === 좌측 영역: 상태 및 실행 제어 ===
        left_section = tk.Frame(main_container, bg=self.style_manager.colors['bg_secondary'])
        left_section.pack(side='left', fill='both', expand=True, padx=(0, 20))
        
        # 상태 표시
        status_frame = tk.Frame(left_section, bg=self.style_manager.colors['bg_secondary'])
        status_frame.pack(anchor='w', pady=(0, 10))
        
        self.status_dot = tk.Label(status_frame, text="●", font=('Segoe UI', 16),
                                  bg=self.style_manager.colors['bg_secondary'],
                                  fg=self.style_manager.colors['accent_red'])
        self.status_dot.pack(side='left', padx=(0, 8))
        
        self.status_label = tk.Label(status_frame, text="중지됨", 
                                    bg=self.style_manager.colors['bg_secondary'],
                                    fg=self.style_manager.colors['accent_red'],
                                    font=('Segoe UI', 12, 'bold'))
        self.status_label.pack(side='left')
        
        # 실행 정보
        self.last_exec_label = tk.Label(left_section, text="마지막 실행: 없음", 
                                       bg=self.style_manager.colors['bg_secondary'],
                                       fg=self.style_manager.colors['text_secondary'],
                                       font=('Segoe UI', 9))
        self.last_exec_label.pack(anchor='w', pady=1)
        
        self.next_exec_label = tk.Label(left_section, text="다음 실행: 없음", 
                                       bg=self.style_manager.colors['bg_secondary'],
                                       fg=self.style_manager.colors['text_secondary'],
                                       font=('Segoe UI', 9))
        self.next_exec_label.pack(anchor='w', pady=1)
        
        self.countdown_label = tk.Label(left_section, text="", 
                                       bg=self.style_manager.colors['bg_secondary'],
                                       fg=self.style_manager.colors['text_secondary'],
                                       font=('Segoe UI', 9))
        self.countdown_label.pack(anchor='w', pady=(1, 15))
        
        # 실행 버튼들
        button_frame = tk.Frame(left_section, bg=self.style_manager.colors['bg_secondary'])
        button_frame.pack(anchor='w')
        
        # 토글 버튼 (자동 실행 시작/중지)
        self.toggle_btn = ttk.Button(button_frame, text="▶ 자동 실행 시작", 
                                    command=self.toggle_scheduler, 
                                    style='Success.TButton')
        self.toggle_btn.pack(side='left', padx=(0, 10))
        
        self.manual_btn = ttk.Button(button_frame, text="⚡ 즉시 실행", 
                                    command=self.manual_execution, 
                                    style='Warning.TButton')
        self.manual_btn.pack(side='left')
        
        # === 우측 영역: 설정 ===
        right_section = tk.Frame(main_container, bg=self.style_manager.colors['bg_secondary'],
                                relief='solid', borderwidth=1, highlightbackground=self.style_manager.colors['border'])
        right_section.pack(side='right', fill='y', padx=(0, 0))
        
        # 설정 제목
        tk.Label(right_section, text="실행 설정", 
                bg=self.style_manager.colors['bg_secondary'],
                fg=self.style_manager.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=15, pady=(8, 10))  # 상단 패딩 줄임
        
        # 실행 주기 설정
        interval_frame = tk.Frame(right_section, bg=self.style_manager.colors['bg_secondary'])
        interval_frame.pack(anchor='w', padx=15, pady=(0, 8))  # 하단 패딩도 약간 줄임
        
        tk.Label(interval_frame, text="실행 주기:", 
                bg=self.style_manager.colors['bg_secondary'],
                fg=self.style_manager.colors['text_primary'],
                font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 5))
        
        interval_input_frame = tk.Frame(interval_frame, bg=self.style_manager.colors['bg_secondary'])
        interval_input_frame.pack(anchor='w')
        
        self.interval_var = tk.StringVar(value=str(self.config.get('execution_interval', 60)))
        interval_combo = ttk.Combobox(interval_input_frame, textvariable=self.interval_var, 
                                     values=['15', '30', '60', '120', '180'], 
                                     style='Modern.TCombobox', width=8, state='readonly')
        interval_combo.pack(side='left', padx=(0, 5))
        
        tk.Label(interval_input_frame, text="분", 
                bg=self.style_manager.colors['bg_secondary'],
                fg=self.style_manager.colors['text_secondary'],
                font=('Segoe UI', 9)).pack(side='left')
        
        # 자동 실행 옵션
        self.immediate_start_var = tk.BooleanVar(value=self.config.get('immediate_start', True))
        immediate_check = tk.Checkbutton(right_section, text="시작 시 즉시 실행", 
                                        variable=self.immediate_start_var,
                                        bg=self.style_manager.colors['bg_secondary'],
                                        fg=self.style_manager.colors['text_secondary'],
                                        selectcolor=self.style_manager.colors['bg_tertiary'],
                                        activebackground=self.style_manager.colors['bg_secondary'],
                                        font=('Segoe UI', 9))
        immediate_check.pack(anchor='w', padx=15, pady=(0, 5))
        
        # 알림 설정 제목
        tk.Label(right_section, text="알림 설정", 
                bg=self.style_manager.colors['bg_secondary'],
                fg=self.style_manager.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=15, pady=(10, 5))
                
        # 이메일 알림 옵션
        self.email_notifications_var = tk.BooleanVar(value=self.config.get('email_notifications', True))
        email_check = tk.Checkbutton(right_section, text="이메일 알림", 
                                    variable=self.email_notifications_var,
                                    bg=self.style_manager.colors['bg_secondary'],
                                    fg=self.style_manager.colors['text_secondary'],
                                    selectcolor=self.style_manager.colors['bg_tertiary'],
                                    activebackground=self.style_manager.colors['bg_secondary'],
                                    font=('Segoe UI', 9))
        email_check.pack(anchor='w', padx=15, pady=(0, 3))
        
        # 텔레그램 알림 옵션
        self.telegram_notifications_var = tk.BooleanVar(value=self.config.get('telegram_notifications', True))
        telegram_check = tk.Checkbutton(right_section, text="텔레그램 알림", 
                                       variable=self.telegram_notifications_var,
                                       bg=self.style_manager.colors['bg_secondary'],
                                       fg=self.style_manager.colors['text_secondary'],
                                       selectcolor=self.style_manager.colors['bg_tertiary'],
                                       activebackground=self.style_manager.colors['bg_secondary'],
                                       font=('Segoe UI', 9))
        telegram_check.pack(anchor='w', padx=15, pady=(0, 10))
        
        # 설정 저장 버튼
        save_btn = ttk.Button(right_section, text="💾 설정 저장", 
                             command=self.save_settings, 
                             style='Primary.TButton')
        save_btn.pack(anchor='w', padx=15, pady=(0, 15))
        
        # === 실행 로그 카드 ===
        log_card = tk.Frame(main_frame, bg=self.style_manager.colors['bg_secondary'], 
                           relief='solid', borderwidth=1, highlightbackground=self.style_manager.colors['border'])
        log_card.pack(fill='both', expand=True, pady=(0, 0))
        
        # 카드 제목
        tk.Label(log_card, text="실행 로그", 
                bg=self.style_manager.colors['bg_secondary'],
                fg=self.style_manager.colors['text_primary'],
                font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=20, pady=(15, 5))
        
        # 로그 제어 버튼들
        log_controls = tk.Frame(log_card, bg=self.style_manager.colors['bg_secondary'])
        log_controls.pack(fill='x', padx=20, pady=(0, 15))
        
        # 왼쪽: 로그 지우기 버튼
        clear_log_btn = ttk.Button(log_controls, text="❌로그 지우기", 
                                  command=self.clear_log, 
                                  style='Primary.TButton', width=15)
        clear_log_btn.pack(side='left')
        
        # 오른쪽: 필터 체크박스들
        filter_frame = tk.Frame(log_controls, bg=self.style_manager.colors['bg_secondary'])
        filter_frame.pack(side='right')
        
        self.show_errors = tk.BooleanVar(value=True)
        self.show_success = tk.BooleanVar(value=True)
        self.show_info = tk.BooleanVar(value=True)
        
        tk.Checkbutton(filter_frame, text="오류", variable=self.show_errors,
                      bg=self.style_manager.colors['bg_secondary'],
                      fg=self.style_manager.colors['text_secondary'],
                      selectcolor=self.style_manager.colors['bg_tertiary'],
                      activebackground=self.style_manager.colors['bg_secondary'],
                      font=('Segoe UI', 10)).pack(side='left', padx=6)
        tk.Checkbutton(filter_frame, text="성공", variable=self.show_success,
                      bg=self.style_manager.colors['bg_secondary'],
                      fg=self.style_manager.colors['text_secondary'],
                      selectcolor=self.style_manager.colors['bg_tertiary'],
                      activebackground=self.style_manager.colors['bg_secondary'],
                      font=('Segoe UI', 10)).pack(side='left', padx=6)
        tk.Checkbutton(filter_frame, text="정보", variable=self.show_info,
                      bg=self.style_manager.colors['bg_secondary'],
                      fg=self.style_manager.colors['text_secondary'],
                      selectcolor=self.style_manager.colors['bg_tertiary'],
                      activebackground=self.style_manager.colors['bg_secondary'],
                      font=('Segoe UI', 10)).pack(side='left', padx=6)
        
        # 로그 텍스트 영역 (높이 증가)
        log_container = tk.Frame(log_card, bg=self.style_manager.colors['bg_secondary'])
        log_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.log_text = tk.Text(log_container, height=15, wrap=tk.WORD,
                               bg=self.style_manager.colors['bg_tertiary'],
                               fg=self.style_manager.colors['text_primary'],
                               font=('JetBrains Mono', 9),
                               insertbackground=self.style_manager.colors['text_primary'],
                               selectbackground=self.style_manager.colors['accent_blue'],
                               selectforeground='white',
                               borderwidth=2,
                               highlightthickness=2,
                               highlightcolor=self.style_manager.colors['border'],      # 포커스 시 테두리
                               highlightbackground=self.style_manager.colors['border'], # 비포커스 시 테두리
                               relief='flat')
        
        scrollbar = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True, padx=(0, 4))
        scrollbar.pack(side='right', fill='y')
        
        # 초기 로그 메시지
        self.add_log("[시작] 게임더하기 계약관리 대시보드가 시작되었습니다.")
        self.add_log("[정보] 모든 시스템이 준비되었습니다.")
    
    def add_log(self, message):
        """로그 메시지 추가 - 색상 코딩 적용"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # 메시지 타입에 따른 색상 결정
        if any(keyword in message for keyword in ['[ERROR]', '[ALERT]', '오류', '실패', 'failed']):
            color = self.style_manager.colors['accent_red']
        elif any(keyword in message for keyword in ['[OK]', '[RESULT]', '성공', '완료', 'success']):
            color = self.style_manager.colors['accent_green']
        elif any(keyword in message for keyword in ['[START]', '[CRAWL]', '시작', 'start']):
            color = self.style_manager.colors['accent_blue']
        elif any(keyword in message for keyword in ['[WAIT]', '[INFO]', 'wait', '대기', '정보']):
            color = self.style_manager.colors['accent_orange']
        else:
            color = self.style_manager.colors['text_primary']
        
        # 로그 태그 생성 (색상별)
        tag_name = f"log_{color.replace('#', '')}"
        self.log_text.tag_configure(tag_name, foreground=color)
        
        # 텍스트 삽입
        start_pos = self.log_text.index(tk.END + "-1c")
        self.log_text.insert(tk.END, log_message)
        end_pos = self.log_text.index(tk.END + "-1c")
        
        # 색상 태그 적용
        self.log_text.tag_add(tag_name, start_pos, end_pos)
        
        # 스크롤을 맨 아래로
        self.log_text.see(tk.END)
        
        # 로그가 너무 길어지면 상위 라인 삭제 (성능 최적화)
        line_count = int(self.log_text.index('end-1c').split('.')[0])
        if line_count > 150:
            self.log_text.delete('1.0', '10.0')  # 한 번에 10줄 삭제
        
        # 콘솔에도 출력
        print(f"[{timestamp}] {message}")
    
    def toggle_scheduler(self):
        """자동 실행 스케줄러 토글"""
        if self.is_running:
            self.stop_scheduler()
        else:
            self.start_scheduler()
    
    def start_scheduler(self):
        """자동 실행 스케줄러 시작"""
        if not self.is_running:
            interval = int(self.interval_var.get())
            immediate_start = self.immediate_start_var.get()
            
            # 기존 작업 제거
            self.scheduler.remove_all_jobs()
            
            # 새로운 작업 추가
            self.scheduler.add_job(
                func=self.execute_crawler,
                trigger="interval",
                minutes=interval,
                id='crawler_job'
            )
            
            self.is_running = True
            self.next_execution = datetime.now() + timedelta(minutes=interval)
            
            self.add_log(f"[OK] 자동 실행이 시작되었습니다. (주기: {interval}분)")
            
            # 상태 변경 애니메이션
            self.animate_status_change("running")
            
            # 토스트 알림
            self.show_toast(f"🚀 자동 실행이 시작되었습니다! (주기: {interval}분)", "success")
            
            # 즉시 실행 옵션 확인
            if immediate_start:
                self.add_log("[START] 첫 번째 실행을 즉시 시작합니다...")
                threading.Thread(target=self.execute_crawler, daemon=True).start()
            else:
                self.add_log(f"[WAIT] {interval}분 후 첫 번째 실행이 시작됩니다.")
            
            self.update_buttons()
    
    def stop_scheduler(self):
        """자동 실행 스케줄러 중지"""
        if self.is_running:
            self.scheduler.remove_all_jobs()
            self.is_running = False
            self.next_execution = None
            
            self.add_log("[STOP] 자동 실행이 중지되었습니다.")
            
            # 상태 변경 애니메이션
            self.animate_status_change("stopped")
            
            # 토스트 알림
            self.show_toast("⏹️ 자동 실행이 중지되었습니다.", "warning")
            
            self.update_buttons()
    
    def manual_execution(self):
        """수동으로 즉시 실행"""
        self.add_log("[START] 수동 실행을 시작합니다...")
        self.show_toast("🔄 수동 실행을 시작합니다...", "info")
        threading.Thread(target=self.execute_crawler, daemon=True).start()
    
    def execute_crawler(self):
        """크롤러 실행 - 실시간 로그 표시"""
        try:
            self.add_log("[CRAWL] 크롤링을 시작합니다...")
            
            # Windows 환경 한글 처리를 위한 설정
            if sys.platform.startswith('win'):
                # Windows에서는 cp949 인코딩 사용
                encoding = 'cp949'
            else:
                encoding = 'utf-8'
            
            # 알림 설정 환경 변수 설정
            env = os.environ.copy()
            env['EMAIL_NOTIFICATIONS'] = str(int(self.config.get('email_notifications', True)))
            env['TELEGRAM_NOTIFICATIONS'] = str(int(self.config.get('telegram_notifications', True)))
            
            # login_and_crawl.py 실행 (실시간 출력, 안전한 인코딩, 환경변수 전달)
            process = subprocess.Popen(['python', 'login_and_crawl.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT,
                                     text=True,
                                     encoding=encoding,
                                     errors='ignore',  # 인코딩 오류 무시
                                     bufsize=1,
                                     env=env)
            
            # 실시간으로 출력 읽기
            output_lines = []
            while True:
                try:
                    line = process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:  # 빈 줄 제외
                            output_lines.append(line)
                            # 대시보드에 실시간 로그 표시 (단순화된 안전한 방식)
                            def safe_add_log(msg):
                                try:
                                    # 한글은 유지하고 문제되는 특수문자만 제거
                                    import re
                                    # 제어문자와 일부 특수 이모지만 제거 (한글과 기본 특수문자는 유지)
                                    clean_msg = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', str(msg))
                                    # 너무 긴 줄은 자르기
                                    if len(clean_msg) > 200:
                                        clean_msg = clean_msg[:200] + "..."
                                    self.add_log(f"[LOG] {clean_msg}")
                                except Exception as e:
                                    self.add_log(f"[INFO] [크롤링 진행 중...]")
                            
                            self.root.after(0, lambda msg=line: safe_add_log(msg))
                    elif process.poll() is not None:
                        break
                except UnicodeDecodeError as e:
                    # 인코딩 오류 발생시 건너뛰기
                    self.root.after(0, lambda: self.add_log("[INFO] [인코딩 오류로 일부 로그 생략]"))
                    continue
                except Exception as e:
                    self.root.after(0, lambda: self.add_log(f"[INFO] [로그 읽기 오류: {str(e)}]"))
                    continue
            
            # 프로세스 완료 대기
            return_code = process.wait()
            
            self.last_execution = datetime.now()
            
            if return_code == 0:
                self.add_log("[OK] 크롤링이 성공적으로 완료되었습니다.")
                
                # 성공 토스트 알림
                self.root.after(0, lambda: self.show_toast("✅ 크롤링이 성공적으로 완료되었습니다!", "success"))
                
                # 주요 결과 요약 표시
                summary_keywords = ['신규 계약', '변경사항', '알림 발송', '업데이트 완료', '크롤링 완료', 
                                   '이메일', '텔레그램', '구글 시트']
                summary_lines = [line for line in output_lines if any(keyword in line for keyword in summary_keywords)]
                if summary_lines:
                    self.add_log("[RESULT] 실행 결과 요약:")
                    for summary in summary_lines[-5:]:  # 최근 5개만
                        self.add_log(f"   • {summary}")
            else:
                self.add_log(f"[ERROR] 크롤링 실행 중 오류 발생 (코드: {return_code})")
                
                # 오류 토스트 알림
                self.root.after(0, lambda: self.show_toast(f"❌ 크롤링 실행 중 오류가 발생했습니다! (코드: {return_code})", "error"))
                
                # 오류 메시지 표시
                error_keywords = ['error', 'exception', 'failed', '오류', '실패', 'traceback', 'modulenotfound']
                error_lines = [line for line in output_lines if any(keyword in line.lower() for keyword in error_keywords)]
                if error_lines:
                    self.add_log("[CRAWL] 오류 상세:")
                    for error in error_lines[-3:]:  # 최근 3개 오류만
                        self.add_log(f"   [ERROR] {error[:100]}...")  # 긴 오류는 자르기
            
            # 다음 실행 시간 업데이트
            if self.is_running:
                interval = int(self.interval_var.get())
                self.next_execution = datetime.now() + timedelta(minutes=interval)
            
        except Exception as e:
            self.add_log(f"[ERROR] 실행 중 예외 발생: {str(e)}")
            self.add_log("[TIP] 문제 해결을 위해 직접 실행해보세요: python login_and_crawl.py")
            
            # 예외 토스트 알림
            self.root.after(0, lambda: self.show_toast(f"❌ 실행 중 예외가 발생했습니다: {str(e)[:50]}...", "error"))
    
    def save_settings(self):
        """설정 저장"""
        try:
            self.config['execution_interval'] = int(self.interval_var.get())
            self.config['immediate_start'] = self.immediate_start_var.get()
            self.config['email_notifications'] = self.email_notifications_var.get()
            self.config['telegram_notifications'] = self.telegram_notifications_var.get()
            self.save_config()
            
            # 알림 설정 로그
            email_status = "활성화" if self.email_notifications_var.get() else "비활성화"
            telegram_status = "활성화" if self.telegram_notifications_var.get() else "비활성화"
            self.add_log(f"[SAVE] 설정이 저장되었습니다. (이메일 알림: {email_status}, 텔레그램 알림: {telegram_status})")
            
            # 토스트 알림
            self.show_toast("💾 설정이 저장되었습니다!", "success")
            
            # 실행 중이면 스케줄러 재시작
            if self.is_running:
                self.stop_scheduler()
                self.start_scheduler()
                
        except ValueError:
            messagebox.showerror("오류", "실행 주기는 숫자로 입력해주세요.")
            self.show_toast("❌ 실행 주기는 숫자로 입력해주세요!", "error")
    
    def update_buttons(self):
        """버튼 상태 업데이트"""
        if self.is_running:
            # 실행 중일 때: 중지 버튼으로 변경
            self.toggle_btn.configure(text="⏹ 자동 실행 중지", style='Danger.TButton')
            self.manual_btn.configure(state='normal')  # 즉시 실행은 계속 가능
        else:
            # 중지 상태일 때: 시작 버튼으로 변경
            self.toggle_btn.configure(text="▶ 자동 실행 시작", style='Success.TButton')
            self.manual_btn.configure(state='normal')
    
    def update_status(self):
        """상태 표시 업데이트"""
        # 실행 상태 - 모던 스타일 적용
        if self.is_running:
            self.status_label.configure(text="실행 중", 
                                       fg=self.style_manager.colors['accent_green'])
            self.status_dot.configure(fg=self.style_manager.colors['accent_green'])
        else:
            self.status_label.configure(text="중지됨", 
                                       fg='#DD5D5C')  # 진한 빨간색으로 변경
            self.status_dot.configure(fg='#DD5D5C')    # 진한 빨간색으로 변경
        
        # 마지막 실행 시간
        if self.last_execution:
            last_str = self.last_execution.strftime("%Y-%m-%d %H:%M:%S")
            self.last_exec_label.configure(text=f"마지막 실행: {last_str}")
        
        # 다음 실행 시간 및 카운트다운
        if self.next_execution and self.is_running:
            next_str = self.next_execution.strftime("%Y-%m-%d %H:%M:%S")
            self.next_exec_label.configure(text=f"다음 실행: {next_str}")
            
            # 카운트다운 계산 - 시각적 강조
            time_left = self.next_execution - datetime.now()
            if time_left.total_seconds() > 0:
                minutes = int(time_left.total_seconds() // 60)
                seconds = int(time_left.total_seconds() % 60)
                # 실행이 임박하면 색상 변경
                if minutes < 1:
                    self.countdown_label.configure(
                        text=f"{minutes}분 {seconds}초 후 실행",
                        fg=self.style_manager.colors['accent_orange'])
                    self.status_dot.configure(fg=self.style_manager.colors['accent_orange'])
                else:
                    self.countdown_label.configure(
                        text=f"{minutes}분 {seconds}초 후 실행",
                        fg=self.style_manager.colors['text_secondary'])
                    self.status_dot.configure(fg=self.style_manager.colors['accent_green'])
            else:
                self.countdown_label.configure(text="")
        else:
            self.next_exec_label.configure(text="다음 실행: 없음")
            self.countdown_label.configure(text="")
        
        # 1초 후 다시 업데이트
        self.root.after(1000, self.update_status)
    
    def on_closing(self):
        """창 닫기 이벤트"""
        if self.is_running:
            if messagebox.askokcancel("종료", "자동 실행이 진행 중입니다. 정말 종료하시겠습니까?"):
                self.scheduler.shutdown()
                self.root.destroy()
        else:
            self.scheduler.shutdown()
            self.root.destroy()
    
    def clear_log(self):
        """로그 텍스트 지우기"""
        self.log_text.delete('1.0', tk.END)
        self.add_log("[INFO] 로그가 초기화되었습니다.")
    
    def show_toast(self, message, toast_type="info", duration=3000):
        """모던 토스트 알림 표시"""
        try:
            # 토스트 윈도우 생성
            toast = tk.Toplevel(self.root)
            toast.withdraw()  # 처음에는 숨김
            toast.overrideredirect(True)  # 윈도우 장식 제거
            toast.attributes('-topmost', True)  # 최상위 표시
            
            # 토스트 크기와 위치 설정
            toast_width = 400
            toast_height = 80
            
            # 화면 우측 하단에 표시
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = screen_width - toast_width - 20
            y = screen_height - toast_height - 100 - (len(self.toast_windows) * 90)
            
            toast.geometry(f"{toast_width}x{toast_height}+{x}+{y}")
            
            # 토스트 타입에 따른 색상 설정
            if toast_type == "success":
                bg_color = '#3B9B60'  # 진한 녹색
                icon = "✅"
            elif toast_type == "error":
                bg_color = '#DD5D5C'  # 진한 빨간색
                icon = "❌"
            elif toast_type == "warning":
                bg_color = '#E67E22'  # 진한 오렌지
                icon = "⚠️"
            else:  # info
                bg_color = '#4677A7'  # 진한 블루
                icon = "ℹ️"
            
            # 토스트 프레임
            toast_frame = tk.Frame(toast, bg=bg_color, relief='flat', borderwidth=0)
            toast_frame.pack(fill='both', expand=True, padx=2, pady=2)
            
            # 그림자 효과
            shadow_frame = tk.Frame(toast, bg=self.style_manager.colors['shadow'], height=2)
            shadow_frame.pack(side='bottom', fill='x')
            
            # 아이콘과 메시지
            content_frame = tk.Frame(toast_frame, bg=bg_color)
            content_frame.pack(fill='both', expand=True, padx=15, pady=10)
            
            icon_label = tk.Label(content_frame, text=icon, font=('Segoe UI', 16),
                                 bg=bg_color, fg='white')
            icon_label.pack(side='left')
            
            msg_label = tk.Label(content_frame, text=message, font=('Segoe UI', 10, 'bold'),
                               bg=bg_color, fg='white', wraplength=300, justify='left')
            msg_label.pack(side='left', padx=(10, 0))
            
            # 닫기 버튼
            close_btn = tk.Label(content_frame, text="×", font=('Segoe UI', 14, 'bold'),
                               bg=bg_color, fg='white', cursor='hand2')
            close_btn.pack(side='right')
            close_btn.bind('<Button-1>', lambda e: self.close_toast(toast))
            
            # 토스트 리스트에 추가
            self.toast_windows.append(toast)
            
            # 토스트 표시 애니메이션 (페이드 인)
            self.animate_toast_in(toast)
            
            # 자동 닫기
            self.root.after(duration, lambda: self.close_toast(toast))
            
        except Exception as e:
            print(f"토스트 표시 오류: {e}")
    
    def animate_toast_in(self, toast):
        """토스트 페이드 인 애니메이션"""
        try:
            toast.deiconify()  # 윈도우 표시
            # 투명도 애니메이션 (Windows에서 지원되는 경우)
            try:
                toast.attributes('-alpha', 0.0)
                for i in range(1, 11):
                    alpha = i / 10.0
                    toast.attributes('-alpha', alpha)
                    toast.update()
                    time.sleep(0.02)
            except:
                # 투명도 미지원시 그냥 표시
                pass
        except:
            pass
    
    def close_toast(self, toast):
        """토스트 닫기"""
        try:
            if toast in self.toast_windows:
                self.toast_windows.remove(toast)
            toast.destroy()
            # 다른 토스트들 위치 재조정
            self.reposition_toasts()
        except:
            pass
    
    def reposition_toasts(self):
        """토스트 위치 재조정"""
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            for i, toast in enumerate(self.toast_windows):
                if toast.winfo_exists():
                    x = screen_width - 400 - 20
                    y = screen_height - 80 - 100 - (i * 90)
                    toast.geometry(f"400x80+{x}+{y}")
        except:
            pass
    
    def animate_status_change(self, new_status):
        """상태 변경 애니메이션"""
        self.status_blink_count = 0
        self.blink_status_indicator()
    
    def blink_status_indicator(self):
        """상태 인디케이터 깜빡임 효과"""
        if self.status_blink_count < 6:  # 3번 깜빡임
            if self.status_blink_count % 2 == 0:
                self.status_dot.configure(fg=self.style_manager.colors['text_muted'])
            else:
                if self.is_running:
                    self.status_dot.configure(fg=self.style_manager.colors['accent_green'])
                else:
                    self.status_dot.configure(fg=self.style_manager.colors['accent_red'])
            
            self.status_blink_count += 1
            self.root.after(200, self.blink_status_indicator)

# Windows 다크 모드 적용을 위한 함수
def apply_dark_title_bar(root):
    """Windows 제목 표시줄과 윈도우 배경을 다크 모드로 변경"""
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            
            # Windows API 함수들
            user32 = ctypes.windll.user32
            dwmapi = ctypes.windll.dwmapi
            
            # 윈도우 핸들 가져오기
            hwnd = user32.GetParent(root.winfo_id())
            
            # DWMWA_USE_IMMERSIVE_DARK_MODE 속성 설정
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_dark_mode = ctypes.c_int(1)  # 1 = 다크 모드, 0 = 라이트 모드
            
            # DwmSetWindowAttribute 함수 호출
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(set_dark_mode),
                ctypes.sizeof(set_dark_mode)
            )
            
            # 제목 표시줄 색상 변경 (창 바탕색과 동일하게)
            DWMWA_CAPTION_COLOR = 35
            dark_color = ctypes.c_int(0x282422)  # #222428를 리틀 엔디안으로 변환
            
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CAPTION_COLOR,
                ctypes.byref(dark_color),
                ctypes.sizeof(dark_color)
            )
            
            # 윈도우 프레임 배경색 설정
            DWMWA_BORDER_COLOR = 34
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_BORDER_COLOR,
                ctypes.byref(dark_color),
                ctypes.sizeof(dark_color)
            )
            
            # 추가 윈도우 배경 설정
            DWMWA_COLOR_DEFAULT = 0x282422  # 배경색 (#222428을 리틀 엔디안으로)
            try:
                # 윈도우 배경 브러시 설정
                gdi32 = ctypes.windll.gdi32
                bg_brush = gdi32.CreateSolidBrush(DWMWA_COLOR_DEFAULT)
                user32.SetClassLongPtrW(hwnd, -10, bg_brush)  # GCL_HBRBACKGROUND = -10
            except:
                pass
            
    except Exception as e:
        print(f"다크 모드 적용 실패: {e}")
        # 실패해도 프로그램은 계속 실행

def main():
    root = tk.Tk()
    app = GameDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 