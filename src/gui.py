"""
GUI модуль — графический интерфейс SSH клиента
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading
import os
import time
import tempfile
import shutil
import ctypes
import ctypes.wintypes as wintypes

import subprocess
import webbrowser
import socket
import base64
import json
import time
from src.ssh import SSHClient
from src.utils import get_timestamp, load_connections, save_connections


class FileSyncer(threading.Thread):
    """Фоновый монитор файла для синхронизации изменений на сервер"""

    def __init__(self, local_path, remote_path, ssh_client, log_callback):
        super().__init__(daemon=True)
        self.local_path = local_path
        self.remote_path = remote_path
        self.ssh_client = ssh_client
        self.log_callback = log_callback
        self.running = True
        try:
            self.last_mtime = os.path.getmtime(local_path)
        except Exception:
            self.last_mtime = 0

    def run(self):
        while self.running:
            try:
                if not os.path.exists(self.local_path):
                    break
                current_mtime = os.path.getmtime(self.local_path)
                if current_mtime > self.last_mtime:
                    success, msg = self.ssh_client.upload_file(self.local_path, self.remote_path)
                    if success:
                        self.last_mtime = current_mtime
                        self.log_callback(f"💾 Синхронизация: {os.path.basename(self.local_path)}", "success")
                    else:
                        self.log_callback(f"⚠️ Ошибка синхронизации: {msg}", "error")
                time.sleep(2)
            except Exception:
                break

    def stop(self):
        self.running = False


class KittyController:
    """Управление Kitty: отправка команд и чтение логов"""

    WM_CHAR = 0x0102
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101

    def __init__(self, log_callback):
        self.log_callback = log_callback
        self.hwnd = None
        self.user32 = ctypes.windll.user32
        self.log_file = None
        self.log_watcher = None
        self.log_watcher_running = False
        self.log_position = 0
        self.root = None

    def start_kitty_with_logging(self, kitty_exe, username, hostname, port, password):
        """Запустить Kitty с логированием"""
        import subprocess

        temp_dir = tempfile.gettempdir()
        self.log_file = os.path.join(temp_dir, "kitty_session.log")

        if os.path.exists(self.log_file):
            try:
                os.remove(self.log_file)
            except Exception:
                pass

        # Запускаем Kitty с логированием (свёрнутым)
        cmd = (
            f'start /min "Kitty" "{kitty_exe}" -ssh {username}@{hostname} '
            f'-P {port} -pw {password} -log "{self.log_file}"'
        )
        self.log_callback(f"🐱 Запуск Kitty...", "info")
        subprocess.Popen(cmd, shell=True)

        time.sleep(1.5)
        self.find_kitty_window()
        self._start_log_watcher()

    def _start_log_watcher(self):
        """Запустить фоновый мониторинг лога"""
        self.log_watcher_running = True
        self.log_position = 0
        self.log_watcher = threading.Thread(target=self._watch_log_file, daemon=True)
        self.log_watcher.start()

    def _watch_log_file(self):
        """Читать новые строки из лог-файла, фильтруя технические строки"""
        import re
        
        # Паттерны для фильтрации
        spinner_pattern = re.compile(r'^[\|/\\\-]$')
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
        timer_pattern = re.compile(r'^\d+[smh]?$')
        progress_pattern = re.compile(r'^\d+%\s*$')
        
        while self.log_watcher_running:
            try:
                if self.log_file and os.path.exists(self.log_file):
                    with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                        f.seek(self.log_position)
                        new_data = f.read()
                        if new_data:
                            self.log_position = f.tell()
                            
                            lines = new_data.split('\n')
                            clean_lines = []
                            for line in lines:
                                clean_line = ansi_pattern.sub('', line)
                                stripped = clean_line.strip()
                                
                                if not stripped:
                                    continue
                                if spinner_pattern.match(stripped):
                                    continue
                                if timer_pattern.match(stripped):
                                    continue
                                if progress_pattern.match(stripped):
                                    continue
                                
                                clean_lines.append(clean_line.strip())
                            
                            # Вывод Kitty не дублируем в журнал — Kitty работает отдельно
                            pass
                                
                time.sleep(0.3)
            except Exception:
                time.sleep(0.5)

    def find_kitty_window(self):
        """Найти окно KiTTY"""
        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
        )

        result = [None]

        def callback(hwnd, lParam):
            if self.user32.IsWindowVisible(hwnd):
                class_name = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(hwnd, class_name, 256)
                if class_name.value == "KiTTY":
                    result[0] = hwnd
                    return False
            return True

        proc = EnumWindowsProc(callback)
        self.user32.EnumWindows(proc, 0)
        self.hwnd = result[0]
        return self.hwnd is not None

    def send_text(self, text):
        """Отправить текст в Kitty через виртуальную клавиатуру Windows"""
        if not self.hwnd:
            if not self.find_kitty_window():
                return False

        if not self.user32.IsWindow(self.hwnd):
            self.hwnd = None
            return False

        KEYEVENTF_KEYUP = 0x0002
        INPUT_KEYBOARD = 1

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ('wVk', wintypes.WORD),
                ('wScan', wintypes.WORD),
                ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD),
                ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG)),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [('type', wintypes.DWORD), ('ki', KEYBDINPUT)]

        # VK коды для символов
        vk_map = {
            'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
            'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
            'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
            'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
            'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
            'z': 0x5A,
            '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
            '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
            ' ': 0x20, '\n': 0x0D, '\r': 0x0D, '\t': 0x09,
            '.': 0xBE, '/': 0xBF, '\\': 0xDC, '-': 0xBD, '_': 0xBD,
            '=': 0xBB, '+': 0xBB, '[': 0xDB, ']': 0xDD,
            ';': 0xBA, ':': 0xBA, "'": 0xDE, '"': 0xDE,
            ',': 0xBC, '<': 0xBC, '>': 0xBE, '?': 0xBF,
            '`': 0xC0, '~': 0xC0, '{': 0xDB, '}': 0xDD, '|': 0xDC,
            '!': 0x31, '@': 0x32, '#': 0x33, '$': 0x34, '%': 0x35,
            '^': 0x36, '&': 0x37, '*': 0x38, '(': 0x39, ')': 0x30,
        }

        for char in text:
            vk_code = vk_map.get(char.lower(), None)
            if vk_code is None:
                # Для русских букв и других символов используем WM_CHAR
                self.user32.PostMessageW(self.hwnd, self.WM_CHAR, ord(char), 0)
                time.sleep(0.02)
            else:
                key_down = INPUT()
                key_down.type = INPUT_KEYBOARD
                key_down.ki = KEYBDINPUT(vk_code, 0, 0, 0, None)

                key_up = INPUT()
                key_up.type = INPUT_KEYBOARD
                key_up.ki = KEYBDINPUT(vk_code, 0, KEYEVENTF_KEYUP, 0, None)

                inputs = (INPUT * 2)(key_down, key_up)
                self.user32.SendInput(2, inputs, ctypes.sizeof(INPUT))
                time.sleep(0.02)

        return True

    def send_command(self, command):
        """Отправить команду в Kitty"""
        success = self.send_text(command)
        if success:
            self.send_text('\n')
        return success

    def stop(self):
        """Остановить мониторинг"""
        self.log_watcher_running = False
        if self.log_watcher:
            self.log_watcher.join(timeout=2)


class SSHApp:
    """Графический интерфейс SSH клиента"""

    def __init__(self, root, connections_file="ssh_connections.json"):
        self.root = root
        self.root.title("SSH Client by Dog Wisdom Project")
        self.root.geometry("680x440")

        self.ssh = SSHClient()
        self.kitty = KittyController(log_callback=self._log)
        self.kitty.root = root
        self.connections_file = connections_file
        self.saved_connections = load_connections(connections_file)
        self.last_profile_file = "last_profile.txt"
        self._desktop_starting = False
        self._desktop_running = False  # PID запущенного сервера

        # Папка временных файлов — в директории проекта
        project_dir = os.path.dirname(os.path.dirname(__file__))
        self.temp_dir = os.path.join(project_dir, "Downloads")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.downloaded_files = set()  # Отслеживаем скачанные файлы

        self.active_syncers = []

        self._setup_styles()
        self._create_widgets()
        self._load_last_profile()
        self._log("=== SSH Client запущен ===", "info")
        self._log("Нажмите '🔗 Подключиться' для входа на сервер", "info")

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """Очистка и закрытие"""
        self.kitty.stop()
        for syncer in self.active_syncers:
            syncer.stop()
        
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
            
        self.root.destroy()

    def _setup_styles(self):
        """Настройка стилей"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

    def _create_widgets(self):
        """Создание элементов интерфейса"""
        self._create_connection_panel()
        self._create_status_area()

    def _create_connection_panel(self):
        """Панель подключения"""
        frame = ttk.LabelFrame(self.root, text="Подключение", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Профиль
        ttk.Label(frame, text="Профиль:").grid(row=0, column=0, padx=5, pady=5)
        self.profile_combo = ttk.Combobox(frame, width=20, state="readonly")
        self.profile_combo['values'] = list(self.saved_connections.keys()) if self.saved_connections else ["Новое подключение"]
        self.profile_combo.current(0)
        self.profile_combo.grid(row=0, column=1, padx=5, pady=5)
        self.profile_combo.bind('<<ComboboxSelected>>', self._on_profile_select)

        ttk.Button(frame, text="💾 Сохранить", command=self._save_connection).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(frame, text="🗑️ Удалить", command=self._delete_connection).grid(row=0, column=3, padx=5, pady=5)

        # Хост
        ttk.Label(frame, text="Хост:").grid(row=1, column=0, padx=5, pady=5)
        self.host_entry = ttk.Entry(frame, width=30)
        self.host_entry.grid(row=1, column=1, padx=5, pady=5)
        self.host_entry.insert(0, "185.")

        # Порт
        ttk.Label(frame, text="Порт:").grid(row=1, column=2, padx=5, pady=5)
        self.port_entry = ttk.Entry(frame, width=10)
        self.port_entry.grid(row=1, column=3, padx=5, pady=5)
        self.port_entry.insert(0, "22")

        # Пользователь
        ttk.Label(frame, text="Пользователь:").grid(row=2, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(frame, width=30)
        self.username_entry.grid(row=2, column=1, padx=5, pady=5)
        self.username_entry.insert(0, "root")

        # Пароль
        ttk.Label(frame, text="Пароль:").grid(row=2, column=2, padx=5, pady=5)
        self.password_entry = ttk.Entry(frame, width=20, show="*")
        self.password_entry.grid(row=2, column=3, padx=5, pady=5)

        # Ключ
        ttk.Label(frame, text="SSH ключ:").grid(row=3, column=0, padx=5, pady=5)
        self.key_file_entry = ttk.Entry(frame, width=30)
        self.key_file_entry.grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Обзор...", command=self._browse_key_file).grid(row=3, column=2, padx=5, pady=5)

        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=10)

        self.connect_btn = ttk.Button(btn_frame, text="🔗 Подключиться", command=self._connect, width=15)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = ttk.Button(btn_frame, text="❌ Отключиться", command=self._disconnect, width=15, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        self.desktop_btn = ttk.Button(btn_frame, text="🌐 Веб-десктоп", command=self._open_web_desktop, width=15)
        self.desktop_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(btn_frame, text="⚪ Не подключено", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=20)

    def _create_status_area(self):
        """Компактная область статуса — только лог"""
        frame = ttk.LabelFrame(self.root, text="Журнал", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", font="Consolas 11", height=8)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        self.output_text.tag_configure("command", foreground="#4ec9b0")
        self.output_text.tag_configure("output", foreground="#d4d4d4")
        self.output_text.tag_configure("error", foreground="#f48771")
        self.output_text.tag_configure("success", foreground="#6a9955")
        self.output_text.tag_configure("info", foreground="#569cd6")

    def _log(self, message, tag="output"):
        """Вывод сообщения"""
        self.output_text.insert(tk.END, f"{message}\n", tag)
        self.output_text.see(tk.END)

    # === Подключение ===

    def _connect(self):
        """Подключение к серверу"""
        hostname = self.host_entry.get().strip()
        port = self.port_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        key_file = self.key_file_entry.get().strip()

        if not hostname or not username:
            messagebox.showerror("Ошибка", "Введите хост и пользователя")
            return

        self._log(f"Подключение к {hostname}:{port}...", "info")
        self.connect_btn.config(state=tk.DISABLED)

        def thread():
            success, message = self.ssh.connect(hostname, int(port), username, password if password else None, key_file if key_file else None)
            self.root.after(0, lambda: self._on_connect_result(success, message, password))

        threading.Thread(target=thread, daemon=True).start()

    def _on_connect_result(self, success, message, password):
        """Результат подключения"""
        self.connect_btn.config(state=tk.NORMAL)

        if success:
            self._log(f"✅ {message}", "success")
            self.status_label.config(text="🟢 Подключено", foreground="green")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self._current_password = password
            profile_name = self.profile_combo.get()
            if profile_name and profile_name != "Новое подключение":
                self._save_last_profile(profile_name)
            self._open_kitty()
        else:
            self._log(f"❌ Ошибка: {message}", "error")
            self.status_label.config(text="⚪ Ошибка подключения", foreground="red")

    def _execute_server_command(self, command: str) -> tuple[bool, str]:
        """Выполнить команду на сервере напрямую через paramiko"""
        try:
            stdin, stdout, stderr = self.ssh.client.exec_command(command, timeout=10)
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')
            if error and not output:
                return False, error
            return True, output
        except Exception as e:
            return False, str(e)

    def _disconnect(self):
        """Отключение"""
        self.kitty.stop()
        for syncer in self.active_syncers:
            syncer.stop()
        self.active_syncers.clear()

        success, message = self.ssh.disconnect()
        self._log(message, "info")
        self.status_label.config(text="⚪ Не подключено", foreground="gray")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)

        # Удаляем временные файлы
        self._cleanup_downloaded_files()

    def _open_kitty(self):
        """Открыть Kitty с логированием и запустить Move Cursor"""
        import os

        hostname = self.host_entry.get().strip()
        port = self.port_entry.get().strip()
        username = self.username_entry.get().strip()
        password = getattr(self, '_current_password', '')

        if not hostname or not username:
            return

        kitty_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kitty.exe")
        if not os.path.exists(kitty_path):
            self._log("⚠️ kitty.exe не найден", "error")
            return

        # Запускаем Kitty с логированием
        self.kitty.start_kitty_with_logging(kitty_path, username, hostname, port, password)

        # Запускаем Move Cursor
        move_cursor_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "move_cursor", "move_cursor.py")
        if os.path.exists(move_cursor_path):
            self._log("📜 Запуск Move Cursor...", "info")
            import subprocess
            subprocess.Popen(f'start /min "Move Cursor" python "{move_cursor_path}"', shell=True)

    def _open_web_desktop(self):
        """Запустить локальный веб-десктоп (Python) и открыть в браузере"""
        if not self.ssh.is_connected:
            self._log("❌ Ошибка: сначала подключитесь к серверу!", "error")
            return

        if self._desktop_starting:
            self._log("⏳ Веб-десктоп уже запускается...", "info")
            return
        self._desktop_starting = True

        import subprocess
        import webbrowser
        import socket
        import base64
        import json
        import sys

        server_url = "http://localhost:8000"

        # Кодируем данные подключения в URL
        connect_data = {
            "h": self.host_entry.get().strip(),
            "p": int(self.port_entry.get().strip()),
            "u": self.username_entry.get().strip(),
            "w": self._current_password if hasattr(self, '_current_password') else "",
        }
        encoded = base64.urlsafe_b64encode(json.dumps(connect_data).encode()).decode()
        url = f"{server_url}/?c={encoded}"

        # Проверяем, запущен ли сервер
        server_running = False
        try:
            sock = socket.create_connection(("localhost", 8000), timeout=1)
            sock.close()
            server_running = True
        except (ConnectionRefusedError, socket.timeout, OSError):
            pass

        if not server_running:
            self._log("🖥️ Запуск веб-десктопа...", "info")
            backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web-desktop", "backend")
            main_py = os.path.join(backend_dir, "main.py")

            if not os.path.exists(main_py):
                self._log("⚠️ main.py не найден", "error")
                self._desktop_starting = False
                return

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # Проверяем, есть ли fastapi в текущем Python
            python_exe = sys.executable
            try:
                import fastapi
            except ImportError:
                # Venv без fastapi — используем глобальный Python
                for path in [
                    r"D:\Program Files\Python312\python.exe",
                    r"C:\Program Files\Python312\python.exe",
                    r"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe",
                ]:
                    if os.path.exists(path):
                        python_exe = path
                        break

            # Логируем вывод uvicorn для отладки
            log_file = os.path.join(backend_dir, "desktop_server.log")

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Python: {python_exe}\n")

            process = subprocess.Popen(
                [python_exe, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=backend_dir,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=open(log_file, 'a', encoding='utf-8'),
                stderr=open(log_file, 'a', encoding='utf-8')
            )

            self._log(f"📝 PID сервера: {process.pid}", "info")

            def wait_and_open():
                import socket
                import time
                import webbrowser

                for i in range(30):
                    time.sleep(0.5)
                    try:
                        sock = socket.create_connection(("localhost", 8000), timeout=1)
                        sock.close()
                        self.root.after(0, lambda: self._log("🌐 Открываю веб-десктоп...", "info"))
                        self.root.after(0, lambda: webbrowser.open(url))
                        self.root.after(0, lambda: setattr(self, '_desktop_starting', False))
                        return
                    except (ConnectionRefusedError, socket.timeout, OSError):
                        continue

                self.root.after(0, lambda: self._log("⚠️ Сервер не ответил: " + url, "error"))
                self.root.after(0, lambda: setattr(self, '_desktop_starting', False))

            threading.Thread(target=wait_and_open, daemon=True).start()
        else:
            self._log("🌐 Открываю веб-десктоп...", "info")
            self._desktop_starting = False
            webbrowser.open(url)

    # === Прочее ===

    def _browse_key_file(self):
        """Выбор SSH ключа"""
        file_path = filedialog.askopenfilename(title="Выберите SSH ключ", filetypes=[("SSH Keys", "*.pem *.key *.ppk"), ("All Files", "*.*")])
        if file_path:
            self.key_file_entry.delete(0, tk.END)
            self.key_file_entry.insert(0, file_path)

    def open_remote_file(self, remote_path):
        """Скачать и открыть файл с сервера"""
        if not self.ssh.is_connected:
            self._log("❌ Нет подключения", "error")
            return

        filename = os.path.basename(remote_path)
        local_path = os.path.join(self.temp_dir, filename)

        self._log(f"⬇️ Скачивание: {filename}...", "info")

        def thread():
            success, msg = self.ssh.download_file(remote_path, local_path)
            if success:
                self.downloaded_files.add(local_path)
                self.root.after(0, lambda: self._on_file_downloaded(local_path, filename))
            else:
                self.root.after(0, lambda: self._log(f"❌ Ошибка: {msg}", "error"))

        threading.Thread(target=thread, daemon=True).start()

    def _on_file_downloaded(self, local_path, filename):
        """Файл скачан — открыть"""
        self._log(f"✅ {filename} скачан", "success")
        try:
            os.startfile(local_path)
            self._log(f"📂 Открыт: {filename}", "success")
        except Exception as e:
            self._log(f"❌ Не удалось открыть: {e}", "error")

    def _cleanup_downloaded_files(self):
        """Удалить все временные файлы"""
        for f in self.downloaded_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass
        self.downloaded_files.clear()
        self._log("🧹 Временные файлы удалены", "info")

    def _save_connection(self):
        """Сохранение профиля"""
        profile_name = simpledialog.askstring("Сохранить профиль", "Введите имя профиля:")
        if profile_name:
            connection = {
                "host": self.host_entry.get(),
                "port": self.port_entry.get(),
                "username": self.username_entry.get(),
                "password": self.password_entry.get(),
                "key_file": self.key_file_entry.get()
            }
            self.saved_connections[profile_name] = connection
            save_connections(self.connections_file, self.saved_connections)
            self.profile_combo['values'] = list(self.saved_connections.keys())
            self.profile_combo.set(profile_name)
            self._save_last_profile(profile_name)
            self._log(f"💾 Профиль '{profile_name}' сохранён", "success")

    def _on_profile_select(self, event):
        """Загрузка профиля"""
        profile_name = self.profile_combo.get()
        if profile_name in self.saved_connections:
            self._apply_profile(profile_name)
            self._save_last_profile(profile_name)

    def _apply_profile(self, profile_name):
        """Применение профиля"""
        if profile_name not in self.saved_connections:
            return
        c = self.saved_connections[profile_name]
        self.host_entry.delete(0, tk.END); self.host_entry.insert(0, c.get("host", ""))
        self.port_entry.delete(0, tk.END); self.port_entry.insert(0, c.get("port", "22"))
        self.username_entry.delete(0, tk.END); self.username_entry.insert(0, c.get("username", "root"))
        self.password_entry.delete(0, tk.END); self.password_entry.insert(0, c.get("password", ""))
        self.key_file_entry.delete(0, tk.END); self.key_file_entry.insert(0, c.get("key_file", ""))

    def _delete_connection(self):
        """Удаление профиля"""
        profile_name = self.profile_combo.get()
        if profile_name in self.saved_connections:
            if messagebox.askyesno("Удалить", f"Удалить '{profile_name}'?"):
                del self.saved_connections[profile_name]
                save_connections(self.connections_file, self.saved_connections)
                self.profile_combo['values'] = list(self.saved_connections.keys()) if self.saved_connections else ["Новое подключение"]
                self.profile_combo.current(0)
                self._log(f"🗑️ Профиль удалён", "info")

    def _load_last_profile(self):
        """Загрузка последнего профиля"""
        import os
        if not os.path.exists(self.last_profile_file):
            if self.saved_connections:
                p = list(self.saved_connections.keys())[0]
                self.profile_combo.set(p)
                self._apply_profile(p)
            return
        try:
            with open(self.last_profile_file, 'r', encoding='utf-8') as f:
                last = f.read().strip()
            if last in self.saved_connections:
                self.profile_combo.set(last)
                self._apply_profile(last)
        except Exception:
            pass

    def _save_last_profile(self, profile_name):
        try:
            with open(self.last_profile_file, 'w', encoding='utf-8') as f:
                f.write(profile_name)
        except Exception:
            pass

