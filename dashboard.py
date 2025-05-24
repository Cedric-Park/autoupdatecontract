import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import os

class GameDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("게임더하기 계약 관리 자동화 대시보드")
        self.root.geometry("800x600")
        
        # 스케줄러 초기화
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # 설정 파일 로드
        self.config = self.load_config()
        
        # 상태 변수들
        self.is_running = False
        self.last_execution = None
        self.next_execution = None
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        
        self.create_widgets()
        self.update_status()
        
    def load_config(self):
        """설정 파일 로드"""
        try:
            with open('dashboard_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 기본 설정
            default_config = {
                "execution_interval": 60,  # 분 단위
                "auto_start": False,
                "notifications_enabled": True
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """설정 파일 저장"""
        if config is None:
            config = self.config
        with open('dashboard_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def create_widgets(self):
        """UI 위젯 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="🎮 게임더하기 계약 관리 자동화 시스템", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # === 상태 표시 영역 ===
        status_frame = ttk.LabelFrame(main_frame, text="📊 실행 상태", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 실행 상태
        self.status_label = ttk.Label(status_frame, text="🔴 중지됨", font=('Arial', 12, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 마지막 실행 시간
        self.last_exec_label = ttk.Label(status_frame, text="마지막 실행: 없음")
        self.last_exec_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 다음 실행 시간
        self.next_exec_label = ttk.Label(status_frame, text="다음 실행: 없음")
        self.next_exec_label.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # 카운트다운
        self.countdown_label = ttk.Label(status_frame, text="", font=('Arial', 10))
        self.countdown_label.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # === 제어 버튼 영역 ===
        control_frame = ttk.LabelFrame(main_frame, text="🎮 제어", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 버튼들
        self.start_btn = ttk.Button(control_frame, text="▶️ 자동 실행 시작", 
                                   command=self.start_scheduler, width=15)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ 자동 실행 중지", 
                                  command=self.stop_scheduler, width=15)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.manual_btn = ttk.Button(control_frame, text="🚀 즉시 실행", 
                                    command=self.manual_execution, width=15)
        self.manual_btn.grid(row=0, column=2, padx=5)
        
        # === 설정 영역 ===
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ 설정", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 실행 주기 설정
        ttk.Label(settings_frame, text="실행 주기:").grid(row=0, column=0, sticky=tk.W)
        
        self.interval_var = tk.StringVar(value=str(self.config.get('execution_interval', 60)))
        interval_combo = ttk.Combobox(settings_frame, textvariable=self.interval_var, 
                                     values=['15', '30', '60', '120', '180'], width=10)
        interval_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="분").grid(row=0, column=2, sticky=tk.W)
        
        save_btn = ttk.Button(settings_frame, text="💾 설정 저장", 
                             command=self.save_settings)
        save_btn.grid(row=0, column=3, padx=10)
        
        # === 통계 영역 ===
        stats_frame = ttk.LabelFrame(main_frame, text="📈 실행 통계", padding="10")
        stats_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text="총 실행: 0회 | 성공: 0회 | 실패: 0회")
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # === 로그 영역 ===
        log_frame = ttk.LabelFrame(main_frame, text="📋 실행 로그", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 로그 텍스트 영역
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 초기 로그 메시지
        self.add_log("🚀 대시보드가 시작되었습니다.")
    
    def add_log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
        # 로그가 너무 길어지면 상위 라인 삭제
        line_count = int(self.log_text.index('end-1c').split('.')[0])
        if line_count > 100:
            self.log_text.delete('1.0', '2.0')
    
    def start_scheduler(self):
        """자동 실행 스케줄러 시작"""
        if not self.is_running:
            interval = int(self.interval_var.get())
            
            # 기존 작업 제거
            self.scheduler.remove_all_jobs()
            
            # 새 작업 추가
            self.scheduler.add_job(
                func=self.execute_crawler,
                trigger="interval",
                minutes=interval,
                id='crawler_job'
            )
            
            self.is_running = True
            self.next_execution = datetime.now() + timedelta(minutes=interval)
            
            self.add_log(f"✅ 자동 실행이 시작되었습니다. (주기: {interval}분)")
            self.update_buttons()
    
    def stop_scheduler(self):
        """자동 실행 스케줄러 중지"""
        if self.is_running:
            self.scheduler.remove_all_jobs()
            self.is_running = False
            self.next_execution = None
            
            self.add_log("⏹️ 자동 실행이 중지되었습니다.")
            self.update_buttons()
    
    def manual_execution(self):
        """수동으로 즉시 실행"""
        self.add_log("🚀 수동 실행을 시작합니다...")
        threading.Thread(target=self.execute_crawler, daemon=True).start()
    
    def execute_crawler(self):
        """크롤러 실행"""
        try:
            self.add_log("🔍 크롤링을 시작합니다...")
            
            # login_and_crawl.py 실행
            result = subprocess.run(['python', 'login_and_crawl.py'], 
                                  capture_output=True, text=True, encoding='utf-8')
            
            self.execution_count += 1
            self.last_execution = datetime.now()
            
            if result.returncode == 0:
                self.success_count += 1
                self.add_log("✅ 크롤링이 성공적으로 완료되었습니다.")
            else:
                self.error_count += 1
                self.add_log(f"❌ 크롤링 실행 중 오류 발생: {result.stderr[:100]}...")
            
            # 다음 실행 시간 업데이트
            if self.is_running:
                interval = int(self.interval_var.get())
                self.next_execution = datetime.now() + timedelta(minutes=interval)
            
        except Exception as e:
            self.error_count += 1
            self.add_log(f"❌ 실행 중 예외 발생: {str(e)}")
    
    def save_settings(self):
        """설정 저장"""
        try:
            self.config['execution_interval'] = int(self.interval_var.get())
            self.save_config()
            self.add_log("💾 설정이 저장되었습니다.")
            
            # 실행 중이면 스케줄러 재시작
            if self.is_running:
                self.stop_scheduler()
                self.start_scheduler()
                
        except ValueError:
            messagebox.showerror("오류", "실행 주기는 숫자로 입력해주세요.")
    
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
        # 실행 상태
        if self.is_running:
            self.status_label.configure(text="🟢 자동 실행 중", foreground="green")
        else:
            self.status_label.configure(text="🔴 중지됨", foreground="red")
        
        # 마지막 실행 시간
        if self.last_execution:
            last_str = self.last_execution.strftime("%Y-%m-%d %H:%M:%S")
            self.last_exec_label.configure(text=f"마지막 실행: {last_str}")
        
        # 다음 실행 시간 및 카운트다운
        if self.next_execution and self.is_running:
            next_str = self.next_execution.strftime("%Y-%m-%d %H:%M:%S")
            self.next_exec_label.configure(text=f"다음 실행: {next_str}")
            
            # 카운트다운 계산
            time_left = self.next_execution - datetime.now()
            if time_left.total_seconds() > 0:
                minutes = int(time_left.total_seconds() // 60)
                seconds = int(time_left.total_seconds() % 60)
                self.countdown_label.configure(text=f"⏰ {minutes}분 {seconds}초 후 실행")
            else:
                self.countdown_label.configure(text="")
        else:
            self.next_exec_label.configure(text="다음 실행: 없음")
            self.countdown_label.configure(text="")
        
        # 통계 업데이트
        self.stats_label.configure(
            text=f"총 실행: {self.execution_count}회 | 성공: {self.success_count}회 | 실패: {self.error_count}회"
        )
        
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

def main():
    root = tk.Tk()
    app = GameDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 