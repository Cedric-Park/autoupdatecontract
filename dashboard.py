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

class ModernStyle:
    """모던 스타일 설정"""
    def __init__(self):
        # 다크 테마 색상 팔레트
        self.colors = {
            'bg_primary': '#1e1e2e',      # 메인 배경 (어두운 보라)
            'bg_secondary': '#313244',    # 카드 배경 (중간 회색)
            'bg_tertiary': '#45475a',     # 버튼 배경 (밝은 회색)
            'accent_blue': '#89b4fa',     # 파란색 액센트
            'accent_green': '#a6e3a1',    # 초록색 액센트
            'accent_red': '#f38ba8',      # 빨간색 액센트
            'accent_orange': '#fab387',   # 주황색 액센트
            'accent_purple': '#cba6f7',   # 보라색 액센트
            'text_primary': '#cdd6f4',    # 메인 텍스트
            'text_secondary': '#a6adc8',  # 보조 텍스트
            'text_muted': '#6c7086',      # 흐린 텍스트
            'border': '#585b70',          # 테두리
            'shadow': '#11111b',          # 그림자
        }
    
    def configure_ttk_style(self):
        """ttk 스타일 설정"""
        style = ttk.Style()
        
        # 전체 테마 설정
        style.theme_use('clam')
        
        # Label 스타일
        style.configure('Title.TLabel', 
                       background=self.colors['bg_primary'],
                       foreground=self.colors['accent_blue'],
                       font=('Segoe UI', 20, 'bold'))
        
        style.configure('Header.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 12, 'bold'))
        
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
        
        # Frame 스타일 - 기본 TLabelFrame 수정
        style.configure('TLabelFrame',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=2,
                       relief='flat',
                       font=('Segoe UI', 11, 'bold'))
        
        style.configure('TLabelFrame.Label',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 11, 'bold'))
        
        style.configure('TFrame',
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        # Button 스타일
        style.configure('Primary.TButton',
                       background=self.colors['accent_blue'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))
        
        style.map('Primary.TButton',
                  background=[('active', '#74c0fc'), ('pressed', '#339af0')])
        
        style.configure('Success.TButton',
                       background=self.colors['accent_green'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))
        
        style.map('Success.TButton',
                  background=[('active', '#8ce99a'), ('pressed', '#51cf66')])
        
        style.configure('Danger.TButton',
                       background=self.colors['accent_red'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))
        
        style.map('Danger.TButton',
                  background=[('active', '#ffc9de'), ('pressed', '#e64980')])
        
        style.configure('Warning.TButton',
                       background=self.colors['accent_orange'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))
        
        style.map('Warning.TButton',
                  background=[('active', '#ffd8a8'), ('pressed', '#fd7e14')])
        
        # Combobox 스타일
        style.configure('Modern.TCombobox',
                       fieldbackground=self.colors['bg_tertiary'],
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       lightcolor=self.colors['border'],
                       darkcolor=self.colors['border'],
                       font=('Segoe UI', 10))
        
        # Checkbutton 스타일
        style.configure('Modern.TCheckbutton',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_secondary'],
                       focuscolor='none',
                       font=('Segoe UI', 10))
        
        return style

class GameDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 게임더하기 계약 관리 자동화 대시보드")
        self.root.geometry("900x800")
        
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
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        
        # 애니메이션 관련 변수
        self.status_blink_count = 0
        self.toast_windows = []
        
        # 설정 로드
        self.config = self.load_config()
        
        # UI 생성
        self.create_widgets()
        
        # 버튼 상태 초기화
        self.update_buttons()
        
        # 상태 업데이트 시작
        self.update_status()
        
        # 환영 토스트 표시
        self.root.after(1000, lambda: self.show_toast("🎉 모던 대시보드에 오신 것을 환영합니다!", "success"))
    
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
        """모던 UI 위젯 생성"""
        # 메인 프레임 (패딩과 색상 개선)
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 타이틀 섹션 (더 크고 세련되게)
        title_frame = tk.Frame(main_frame, bg=self.style_manager.colors['bg_primary'])
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 30))
        
        title_label = ttk.Label(title_frame, text="🎮 게임더하기 계약 관리", 
                               style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="자동화 대시보드 v2.0 Modern", 
                                  font=('Segoe UI', 14), 
                                  background=self.style_manager.colors['bg_primary'],
                                  foreground=self.style_manager.colors['text_muted'])
        subtitle_label.pack()
        
        # === 상태 카드 ===
        status_card = ttk.LabelFrame(main_frame, text="📊 실행 상태", padding="20")
        status_card.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 상태 표시를 더 시각적으로
        status_container = tk.Frame(status_card, bg=self.style_manager.colors['bg_secondary'])
        status_container.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 상태 인디케이터 추가
        indicator_frame = tk.Frame(status_container, bg=self.style_manager.colors['bg_secondary'])
        indicator_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 상태 도트 (시각적 인디케이터)
        self.status_dot = tk.Label(indicator_frame, text="●", font=('Segoe UI', 20),
                                  bg=self.style_manager.colors['bg_secondary'],
                                  fg=self.style_manager.colors['accent_red'])
        self.status_dot.grid(row=0, column=0, padx=(0, 10))
        
        self.status_label = ttk.Label(indicator_frame, text="🔴 중지됨", 
                                     style='Error.TLabel')
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # 정보 라벨들을 더 깔끔하게
        info_frame = tk.Frame(status_card, bg=self.style_manager.colors['bg_secondary'])
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.last_exec_label = ttk.Label(info_frame, text="마지막 실행: 없음", 
                                        style='Body.TLabel')
        self.last_exec_label.grid(row=0, column=0, sticky=tk.W, pady=3)
        
        self.next_exec_label = ttk.Label(info_frame, text="다음 실행: 없음", 
                                        style='Body.TLabel')
        self.next_exec_label.grid(row=1, column=0, sticky=tk.W, pady=3)
        
        self.countdown_label = ttk.Label(info_frame, text="", 
                                        style='Body.TLabel',
                                        font=('Segoe UI', 10, 'italic'))
        self.countdown_label.grid(row=2, column=0, sticky=tk.W, pady=3)
        
        # === 제어 버튼 카드 ===
        control_card = ttk.LabelFrame(main_frame, text="🎮 제어", padding="20")
        control_card.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 버튼들을 그리드로 더 깔끔하게 배치
        button_frame = tk.Frame(control_card, bg=self.style_manager.colors['bg_secondary'])
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 버튼 그룹 중앙 정렬
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)
        
        self.start_btn = ttk.Button(button_frame, text="▶️ 자동 실행 시작", 
                                   command=self.start_scheduler, 
                                   style='Success.TButton', width=18)
        self.start_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️ 자동 실행 중지", 
                                  command=self.stop_scheduler, 
                                  style='Danger.TButton', width=18)
        self.stop_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.manual_btn = ttk.Button(button_frame, text="🚀 즉시 실행", 
                                    command=self.manual_execution, 
                                    style='Warning.TButton', width=18)
        self.manual_btn.grid(row=1, column=1, columnspan=2, pady=(5, 0))
        
        # === 설정 카드 ===
        settings_card = ttk.LabelFrame(main_frame, text="⚙️ 설정", padding="20")
        settings_card.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 실행 주기 설정을 더 세련되게
        interval_frame = tk.Frame(settings_card, bg=self.style_manager.colors['bg_secondary'])
        interval_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        interval_frame.grid_columnconfigure(4, weight=1)  # 여백 추가
        
        ttk.Label(interval_frame, text="실행 주기:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W)
        
        self.interval_var = tk.StringVar(value=str(self.config.get('execution_interval', 60)))
        interval_combo = ttk.Combobox(interval_frame, textvariable=self.interval_var, 
                                     values=['15', '30', '60', '120', '180'], 
                                     style='Modern.TCombobox', width=8, state='readonly')
        interval_combo.grid(row=0, column=1, padx=(10, 5))
        
        ttk.Label(interval_frame, text="분", style='Body.TLabel').grid(row=0, column=2, sticky=tk.W)
        
        save_btn = ttk.Button(interval_frame, text="💾 설정 저장", 
                             command=self.save_settings, 
                             style='Primary.TButton', width=12)
        save_btn.grid(row=0, column=3, padx=(20, 0))
        
        # 즉시 실행 옵션
        self.immediate_start_var = tk.BooleanVar(value=self.config.get('immediate_start', True))
        immediate_check = ttk.Checkbutton(settings_card, text="자동 실행 시작 시 즉시 1회 실행", 
                                         variable=self.immediate_start_var,
                                         style='Modern.TCheckbutton')
        immediate_check.grid(row=1, column=0, sticky=tk.W)
        
        # === 통계 카드 ===
        stats_card = ttk.LabelFrame(main_frame, text="📈 실행 통계", padding="20")
        stats_card.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 통계를 시각적으로 표시
        stats_container = tk.Frame(stats_card, bg=self.style_manager.colors['bg_secondary'])
        stats_container.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 통계 메인 라벨
        self.stats_label = ttk.Label(stats_container, text="실행 기록 없음", 
                                    style='Header.TLabel')
        self.stats_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # 프로그레스 바 스타일 (성공률 표시용)
        self.style.configure('Success.Horizontal.TProgressbar',
                           background=self.style_manager.colors['accent_green'],
                           troughcolor=self.style_manager.colors['bg_tertiary'],
                           borderwidth=0,
                           lightcolor=self.style_manager.colors['accent_green'],
                           darkcolor=self.style_manager.colors['accent_green'])
        
        # 성공률 프로그레스 바
        progress_frame = tk.Frame(stats_container, bg=self.style_manager.colors['bg_secondary'])
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Label(progress_frame, text="성공률:", 
                 style='Body.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.success_progress = ttk.Progressbar(progress_frame, style='Success.Horizontal.TProgressbar',
                                               length=200, mode='determinate')
        self.success_progress.grid(row=0, column=1, sticky=tk.W)
        
        self.success_rate_label = ttk.Label(progress_frame, text="0%", 
                                           style='Body.TLabel')
        self.success_rate_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # === 로그 카드 ===
        log_card = ttk.LabelFrame(main_frame, text="📋 실행 로그", padding="20")
        log_card.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 로그 제어 버튼들
        log_controls = tk.Frame(log_card, bg=self.style_manager.colors['bg_secondary'])
        log_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        clear_log_btn = ttk.Button(log_controls, text="🗑️ 로그 지우기", 
                                  command=self.clear_log, 
                                  style='Primary.TButton', width=12)
        clear_log_btn.grid(row=0, column=0, sticky=tk.W)
        
        # 로그 필터 체크박스들
        filter_frame = tk.Frame(log_controls, bg=self.style_manager.colors['bg_secondary'])
        filter_frame.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))
        
        self.show_errors = tk.BooleanVar(value=True)
        self.show_success = tk.BooleanVar(value=True)
        self.show_info = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(filter_frame, text="오류", variable=self.show_errors,
                       style='Modern.TCheckbutton').grid(row=0, column=0, padx=5)
        ttk.Checkbutton(filter_frame, text="성공", variable=self.show_success,
                       style='Modern.TCheckbutton').grid(row=0, column=1, padx=5)
        ttk.Checkbutton(filter_frame, text="정보", variable=self.show_info,
                       style='Modern.TCheckbutton').grid(row=0, column=2, padx=5)
        
        # 로그 텍스트 영역을 더 모던하게
        log_container = tk.Frame(log_card, bg=self.style_manager.colors['bg_secondary'])
        log_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_container, height=10, wrap=tk.WORD,
                               bg=self.style_manager.colors['bg_tertiary'],
                               fg=self.style_manager.colors['text_primary'],
                               font=('Consolas', 9),
                               insertbackground=self.style_manager.colors['accent_blue'],
                               selectbackground=self.style_manager.colors['accent_blue'],
                               selectforeground='white',
                               borderwidth=0,
                               highlightthickness=1,
                               highlightcolor=self.style_manager.colors['accent_blue'])
        
        scrollbar = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)
        log_controls.columnconfigure(1, weight=1)
        
        # 카드들이 동적으로 늘어나도록
        for i in range(6):
            main_frame.rowconfigure(i, weight=0)
        main_frame.rowconfigure(5, weight=1)  # 로그 영역만 확장
        
        # 초기 로그 메시지
        self.add_log("[START] 모던 대시보드 v2.0이 시작되었습니다.")
        self.add_log("[INFO] 새로운 UI 디자인과 향상된 기능을 경험해보세요!")
    
    def clean_log_message(self, message):
        """로그 메시지에서 이모지 제거 (대시보드 표시용)"""
        # 일반적인 이모지 패턴 제거
        emoji_pattern = re.compile("["
                                 u"\U0001F600-\U0001F64F"  # 감정
                                 u"\U0001F300-\U0001F5FF"  # 기호 & 픽토그램
                                 u"\U0001F680-\U0001F6FF"  # 교통 & 지도
                                 u"\U0001F1E0-\U0001F1FF"  # 국기
                                 u"\U00002600-\U000026FF"  # 기타 기호
                                 u"\U00002700-\U000027BF"  # 딩배트
                                 "]+", flags=re.UNICODE)
        return emoji_pattern.sub('', message).strip()
    
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
        elif any(keyword in message for keyword in ['[WAIT]', '[INFO]', 'wait', '대기']):
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
            import sys
            if sys.platform.startswith('win'):
                # Windows에서는 cp949 인코딩 사용
                encoding = 'cp949'
            else:
                encoding = 'utf-8'
            
            # login_and_crawl.py 실행 (실시간 출력, 안전한 인코딩)
            process = subprocess.Popen(['python', 'login_and_crawl.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT,
                                     text=True,
                                     encoding=encoding,
                                     errors='ignore',  # 인코딩 오류 무시
                                     bufsize=1)
            
            # 실시간으로 출력 읽기
            output_lines = []
            while True:
                try:
                    line = process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:  # 빈 줄 제외
                            output_lines.append(line)
                            # 대시보드에 실시간 로그 표시 (안전한 방식)
                            def safe_add_log(msg):
                                try:
                                    # 이모지 제거 후 로그 표시
                                    clean_msg = self.clean_log_message(msg)
                                    self.add_log(f"[LOG] {clean_msg}")
                                except:
                                    self.add_log(f"[LOG] [로그 표시 오류]")
                            
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
            
            self.execution_count += 1
            self.last_execution = datetime.now()
            
            if return_code == 0:
                self.success_count += 1
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
                self.error_count += 1
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
            self.error_count += 1
            self.add_log(f"[ERROR] 실행 중 예외 발생: {str(e)}")
            self.add_log("[TIP] 문제 해결을 위해 직접 실행해보세요: python login_and_crawl.py")
            
            # 예외 토스트 알림
            self.root.after(0, lambda: self.show_toast(f"❌ 실행 중 예외가 발생했습니다: {str(e)[:50]}...", "error"))
    
    def save_settings(self):
        """설정 저장"""
        try:
            self.config['execution_interval'] = int(self.interval_var.get())
            self.config['immediate_start'] = self.immediate_start_var.get()
            self.save_config()
            self.add_log("[SAVE] 설정이 저장되었습니다.")
            
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
            self.start_btn.configure(state='disabled')
            self.stop_btn.configure(state='normal')
        else:
            self.start_btn.configure(state='normal')
            self.stop_btn.configure(state='disabled')
    
    def update_status(self):
        """상태 표시 업데이트"""
        # 실행 상태 - 모던 스타일 적용
        if self.is_running:
            self.status_label.configure(text="🟢 자동 실행 중", style='Success.TLabel')
            self.status_dot.configure(fg=self.style_manager.colors['accent_green'])
        else:
            self.status_label.configure(text="🔴 중지됨", style='Error.TLabel')
            self.status_dot.configure(fg=self.style_manager.colors['accent_red'])
        
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
                        text=f"⏰ {minutes}분 {seconds}초 후 실행",
                        foreground=self.style_manager.colors['accent_orange'])
                    self.status_dot.configure(fg=self.style_manager.colors['accent_orange'])
                else:
                    self.countdown_label.configure(
                        text=f"⏰ {minutes}분 {seconds}초 후 실행",
                        foreground=self.style_manager.colors['text_secondary'])
                    self.status_dot.configure(fg=self.style_manager.colors['accent_green'])
            else:
                self.countdown_label.configure(text="")
        else:
            self.next_exec_label.configure(text="다음 실행: 없음")
            self.countdown_label.configure(text="")
        
        # 통계 업데이트 - 색상 강조 및 프로그레스 바
        total = self.execution_count
        success = self.success_count
        error = self.error_count
        
        if total == 0:
            stats_text = "실행 기록 없음"
            stats_color = self.style_manager.colors['text_muted']
            success_rate = 0
            self.success_progress['value'] = 0
            self.success_rate_label.configure(text="0%", 
                                            foreground=self.style_manager.colors['text_muted'])
        else:
            success_rate = (success / total * 100) if total > 0 else 0
            stats_text = f"총 실행: {total}회 | 성공: {success}회 | 실패: {error}회"
            
            # 성공률에 따라 색상 변경
            if success_rate >= 90:
                stats_color = self.style_manager.colors['accent_green']
                progress_style = 'Success.Horizontal.TProgressbar'
                rate_color = self.style_manager.colors['accent_green']
            elif success_rate >= 70:
                stats_color = self.style_manager.colors['accent_orange']
                # 주황색 프로그레스 바 스타일
                self.style.configure('Warning.Horizontal.TProgressbar',
                                   background=self.style_manager.colors['accent_orange'],
                                   troughcolor=self.style_manager.colors['bg_tertiary'],
                                   borderwidth=0)
                progress_style = 'Warning.Horizontal.TProgressbar'
                rate_color = self.style_manager.colors['accent_orange']
            else:
                stats_color = self.style_manager.colors['accent_red']
                # 빨간색 프로그레스 바 스타일
                self.style.configure('Error.Horizontal.TProgressbar',
                                   background=self.style_manager.colors['accent_red'],
                                   troughcolor=self.style_manager.colors['bg_tertiary'],
                                   borderwidth=0)
                progress_style = 'Error.Horizontal.TProgressbar'
                rate_color = self.style_manager.colors['accent_red']
            
            # 프로그레스 바 업데이트
            self.success_progress.configure(style=progress_style)
            self.success_progress['value'] = success_rate
            self.success_rate_label.configure(text=f"{success_rate:.1f}%", 
                                            foreground=rate_color)
        
        self.stats_label.configure(text=stats_text, foreground=stats_color)
        
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
                bg_color = self.style_manager.colors['accent_green']
                icon = "✅"
            elif toast_type == "error":
                bg_color = self.style_manager.colors['accent_red']
                icon = "❌"
            elif toast_type == "warning":
                bg_color = self.style_manager.colors['accent_orange']
                icon = "⚠️"
            else:  # info
                bg_color = self.style_manager.colors['accent_blue']
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

def main():
    root = tk.Tk()
    app = GameDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 