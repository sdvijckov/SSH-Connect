"""
GUI модуль — графический интерфейс SSH клиента
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading
import os

from src.ssh import SSHClient
from src.terminal import open_terminal
from src.utils import get_timestamp, load_connections, save_connections


class SSHApp:
    """Графический интерфейс SSH клиента"""

    QUICK_COMMANDS = [
        ("📊uptime", "uptime"),
        ("💾df -h", "df -h"),
        ("📁ls -la", "ls -la"),
        ("🔝top", "top -b -n 1"),
        ("🌡️free -h", "free -h"),
        ("📦apt update", "sudo apt update"),
        ("🐍python3 --version", "python3 --version"),
        ("📝tail logs", "tail -f /var/log/syslog"),
    ]

    def __init__(self, root: tk.Tk, connections_file: str = "ssh_connections.json"):
        self.root = root
        self.root.title("SSH Client by Dog Wisdom Project")
        self.root.geometry("1200x700")

        self.ssh = SSHClient()
        self.command_history = []
        self.history_index = 0
        self.connections_file = connections_file
        self.saved_connections = load_connections(connections_file)
        self.home_dir = "/home/sheldon"
        self.last_profile_file = "last_profile.txt"  # Файл для последнего профиля

        self._setup_styles()
        self._create_widgets()
        self._load_last_profile()  # Загружаем последний профиль
        self._log("=== SSH Client запущен ===", "info")
        self._log("Нажмите '🔗 Подключиться' для входа на сервер", "info")

    def _setup_styles(self):
        """Настройка стилей"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

    def _create_widgets(self):
        """Создание элементов интерфейса"""
        self._create_connection_panel()
        self._create_main_area()
        self._create_quick_commands()

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

        self.gui_btn = ttk.Button(btn_frame, text="🖥️ Открыть GUI", command=self._open_gui, width=15, state=tk.DISABLED)
        self.gui_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = ttk.Button(btn_frame, text="❌ Отключиться", command=self._disconnect, width=15, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(btn_frame, text="⚪ Не подключено", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=20)

    def _on_paste(self, event):
        """Вставка из буфера обмена через Tkinter"""
        widget = event.widget
        try:
            # Получаем текст из буфера Tkinter
            text = widget.clipboard_get()
            widget.insert(tk.INSERT, text)
        except:
            pass
        return 'break'  # Блокируем стандартную обработку

    def _create_main_area(self):
        """Основная область (файлы)"""
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Инфо
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding=10)
        main_frame.add(info_frame, weight=1)

        self.info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, bg="#f5f5f5", fg="#333", font="Arial 10")
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.insert(tk.END, "📋 Инструкция:\n\n")
        self.info_text.insert(tk.END, "1. Введите данные подключения\n")
        self.info_text.insert(tk.END, "2. Нажмите '🔗 Подключиться'\n")
        self.info_text.insert(tk.END, "3. Kitty откроется автоматически\n")
        self.info_text.insert(tk.END, "4. Для GUI нажмите '🖥️ Открыть GUI'\n\n")
        self.info_text.insert(tk.END, "📁 Файлы:\n")
        self.info_text.insert(tk.END, "• Двойной клик — просмотр (cat)\n")
        self.info_text.insert(tk.END, "• ⬆️ Загрузить — файл на сервер\n")
        self.info_text.insert(tk.END, "• ⬇️ Скачать — файл на компьютер\n")

        # Файлы
        files_frame = ttk.LabelFrame(main_frame, text="Файлы на сервере", padding=10)
        main_frame.add(files_frame, weight=1)

        self.path_label = ttk.Label(files_frame, text="Путь: ~", font="Consolas 10")
        self.path_label.pack(anchor=tk.W, pady=(0, 5))

        self.files_listbox = tk.Listbox(
            files_frame, font="Consolas 10", bg="#252526", fg="#d4d4d4", selectbackground="#094771"
        )
        self.files_listbox.pack(fill=tk.BOTH, expand=True)
        self.files_listbox.bind('<Double-Button-1>', self._on_file_double_click)

        # Кнопки файлов
        files_btn_frame = ttk.Frame(files_frame)
        files_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(files_btn_frame, text="📁 Обновить", command=self._refresh_files, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(files_btn_frame, text="⬆️ Загрузить", command=self._upload_file, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(files_btn_frame, text="⬇️ Скачать", command=self._download_file, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(files_btn_frame, text="📂 Домой", command=self._go_home, width=10).pack(side=tk.LEFT, padx=2)

    def _create_quick_commands(self):
        """Панель быстрых команд"""
        # Пустая панель (можно добавить быстрые команды позже)

    def _log(self, message: str, tag: str = "output"):
        """Вывод сообщения"""
        timestamp = get_timestamp()
        self.info_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.info_text.see(tk.END)

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

    def _on_connect_result(self, success: bool, message: str, password: str):
        """Результат подключения"""
        self.connect_btn.config(state=tk.NORMAL)

        if success:
            self._log(f"✅ {message}", "success")
            self.status_label.config(text="🟢 Подключено", foreground="green")
            self.connect_btn.config(state=tk.DISABLED)
            self.gui_btn.config(state=tk.NORMAL)  # Активируем кнопку GUI
            self.disconnect_btn.config(state=tk.NORMAL)
            self._current_password = password
            
            # Сохраняем последний профиль
            profile_name = self.profile_combo.get()
            if profile_name and profile_name != "Новое подключение":
                self._save_last_profile(profile_name)
            
            self._refresh_files()
            
            # Открываем Kitty через небольшую паузу
            self.root.after(300, self._open_kitty)
        else:
            self._log(f"❌ Ошибка: {message}", "error")
            self.status_label.config(text="⚪ Ошибка подключения", foreground="red")

    def _disconnect(self):
        """Отключение"""
        success, message = self.ssh.disconnect()
        self._log(message, "info")
        self.status_label.config(text="⚪ Не подключено", foreground="gray")
        self.connect_btn.config(state=tk.NORMAL)
        self.gui_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.files_listbox.delete(0, tk.END)
        self.path_label.config(text="Путь: ~")

    def _open_vnc(self):
        """Открыть VNC Viewer"""
        import subprocess
        import os

        hostname = self.host_entry.get().strip()

        if not hostname:
            self._log("❌ Нет данных подключения", "error")
            return

        # Путь к VNC Viewer в папке проекта
        vnc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vncviewer.exe")
        
        # Проверка наличия vncviewer.exe
        if not os.path.exists(vnc_path):
            self._log(f"❌ vncviewer.exe не найден:\n{vnc_path}", "error")
            return

        # Команда запуска (порт 5901 для :1)
        cmd = f'"{vnc_path}" {hostname}::5901'

        self._log(f"🖥️ Запуск VNC: {hostname}:5901", "info")
        subprocess.Popen(cmd, shell=True)

    def _open_gui(self):
        """Перезапустить VNC и открыть VNC Viewer"""
        if not self.ssh.is_connected:
            self._log("❌ Сначала подключитесь к серверу", "error")
            return

        hostname = self.host_entry.get().strip()

        self._log("🔄 Перезапуск VNC...", "info")

        def thread():
            import subprocess
            import time

            # Перезапуск VNC на сервере
            self.ssh.execute_command("vncserver -kill :1")
            self.ssh.execute_command("vncserver -kill :2")
            time.sleep(1)
            self.ssh.execute_command("vncserver :1 -geometry 1280x800 -depth 24")

            # Пауза чтобы VNC успел запуститься
            time.sleep(2)

            # Запуск VNC Viewer
            vnc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vncviewer.exe")
            if os.path.exists(vnc_path):
                cmd = f'"{vnc_path}" {hostname}::5901'
                subprocess.Popen(cmd, shell=True)

            self.root.after(0, lambda: self._log("✅ GUI готов", "success"))

        threading.Thread(target=thread, daemon=True).start()

    def _open_kitty(self):
        """Открыть Kitty с паролем"""
        import subprocess

        hostname = self.host_entry.get().strip()
        port = self.port_entry.get().strip()
        username = self.username_entry.get().strip()
        password = getattr(self, '_current_password', '')

        if not hostname or not username:
            messagebox.showerror("Ошибка", "Нет данных подключения")
            return

        # Путь к kitty.exe (в папке проекта)
        import os
        kitty_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kitty.exe")
        
        # Проверка наличия kitty.exe
        if not os.path.exists(kitty_path):
            messagebox.showerror("Ошибка", f"kitty.exe не найден:\n{kitty_path}")
            return

        # Команда запуска (свёрнутое окно /min)
        cmd = f'start /min "Kitty" "{kitty_path}" -ssh {username}@{hostname} -P {port} -pw {password}'

        self._log(f"🐱 Запуск Kitty: {username}@{hostname}:{port}", "info")
        subprocess.Popen(cmd, shell=True)

    # === Команды ===

    def _copy_command(self, command: str):
        """Копирование команды"""
        self.root.clipboard_clear()
        self.root.clipboard_append(command)
        self._log(f"📋 Команда скопирована: {command}", "success")

    # === Файлы ===

    def _refresh_files(self):
        """Обновление списка файлов"""
        if not self.ssh.is_connected:
            return

        success, files = self.ssh.list_directory()
        if success:
            self.files_listbox.delete(0, tk.END)
            for file in sorted(files):
                self.files_listbox.insert(tk.END, file)

    def _on_file_double_click(self, event):
        """Двойной клик по файлу"""
        selection = self.files_listbox.curselection()
        if selection:
            filename = self.files_listbox.get(selection[0])
            if not filename.startswith('.'):
                self._copy_command(f"cat {filename}")
                self._log(f"📋 Команда cat {filename} скопирована", "info")

    def _upload_file(self):
        """Загрузка файла"""
        if not self.ssh.is_connected:
            messagebox.showwarning("Внимание", "Сначала подключитесь к серверу")
            return

        file_path = filedialog.askopenfilename(title="Выберите файл для загрузки")
        if file_path:
            filename = os.path.basename(file_path)
            remote_path = f"{self.home_dir}/{filename}"

            def thread():
                success, message = self.ssh.upload_file(file_path, remote_path)
                self.root.after(0, lambda: self._on_upload_result(success, message))

            threading.Thread(target=thread, daemon=True).start()

    def _on_upload_result(self, success: bool, message: str):
        """Результат загрузки"""
        if success:
            self._log(f"✅ {message}", "success")
            self._refresh_files()
        else:
            self._log(f"❌ Ошибка: {message}", "error")

    def _download_file(self):
        """Скачивание файла"""
        if not self.ssh.is_connected:
            messagebox.showwarning("Внимание", "Сначала подключитесь к серверу")
            return

        selection = self.files_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите файл для скачивания")
            return

        filename = self.files_listbox.get(selection[0])
        local_path = filedialog.asksaveasfilename(title="Сохранить файл как", initialfile=filename)

        if local_path:
            remote_path = f"{self.home_dir}/{filename}"

            def thread():
                success, message = self.ssh.download_file(remote_path, local_path)
                self.root.after(0, lambda: self._on_download_result(success, message))

            threading.Thread(target=thread, daemon=True).start()

    def _on_download_result(self, success: bool, message: str):
        """Результат скачивания"""
        if success:
            self._log(f"✅ {message}", "success")
        else:
            self._log(f"❌ Ошибка: {message}", "error")

    def _go_home(self):
        """Домой"""
        self._copy_command("cd ~")

    # === Профили ===

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
            self._save_last_profile(profile_name)  # Сохраняем как последний
            self._log(f"💾 Профиль '{profile_name}' сохранён", "success")

    def _on_profile_select(self, event):
        """Загрузка профиля"""
        profile_name = self.profile_combo.get()
        if profile_name in self.saved_connections:
            self._apply_profile(profile_name)
            self._save_last_profile(profile_name)  # Сохраняем как последний

    def _load_last_profile(self):
        """Загрузка последнего использованного профиля"""
        import os
        if not os.path.exists(self.last_profile_file):
            # Если нет файла, но есть профили — загружаем первый
            if self.saved_connections:
                first_profile = list(self.saved_connections.keys())[0]
                self.profile_combo.set(first_profile)
                self._apply_profile(first_profile)
            return

        try:
            with open(self.last_profile_file, 'r', encoding='utf-8') as f:
                last_profile = f.read().strip()

            if last_profile in self.saved_connections:
                self.profile_combo.set(last_profile)
                self._apply_profile(last_profile)
                self._log(f"💾 Загружен последний профиль: {last_profile}", "info")
            elif self.saved_connections:
                # Профиль не найден, загружаем первый
                first_profile = list(self.saved_connections.keys())[0]
                self.profile_combo.set(first_profile)
                self._apply_profile(first_profile)
        except Exception:
            pass

    def _save_last_profile(self, profile_name: str):
        """Сохранение последнего использованного профиля"""
        try:
            with open(self.last_profile_file, 'w', encoding='utf-8') as f:
                f.write(profile_name)
        except Exception:
            pass

    def _apply_profile(self, profile_name: str):
        """Применение профиля к полям"""
        if profile_name not in self.saved_connections:
            return

        connection = self.saved_connections[profile_name]
        self.host_entry.delete(0, tk.END)
        self.host_entry.insert(0, connection.get("host", ""))
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, connection.get("port", "22"))
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, connection.get("username", "root"))
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, connection.get("password", ""))
        self.key_file_entry.delete(0, tk.END)
        self.key_file_entry.insert(0, connection.get("key_file", ""))

    def _delete_connection(self):
        """Удаление профиля"""
        profile_name = self.profile_combo.get()
        if profile_name in self.saved_connections:
            if messagebox.askyesno("Удалить профиль", f"Удалить профиль '{profile_name}'?"):
                del self.saved_connections[profile_name]
                save_connections(self.connections_file, self.saved_connections)

                self.profile_combo['values'] = list(self.saved_connections.keys()) if self.saved_connections else ["Новое подключение"]
                self.profile_combo.current(0)
                self._log(f"🗑️ Профиль '{profile_name}' удалён", "info")

    # === Прочее ===

    def _copy_ssh_command(self):
        """Копирование SSH команды"""
        hostname = self.host_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        port = self.port_entry.get().strip()

        if not hostname or not username:
            messagebox.showerror("Ошибка", "Сначала введите хост и пользователя")
            return

        ssh_command = f"ssh {username}@{hostname} -p {port}"
        self.root.clipboard_clear()
        self.root.clipboard_append(ssh_command)
        if password:
            self.root.clipboard_append(f"\n{password}")

        self._log(f"📋 Команда скопирована: {ssh_command}", "success")

    def _browse_key_file(self):
        """Выбор SSH ключа"""
        file_path = filedialog.askopenfilename(
            title="Выберите SSH ключ",
            filetypes=[("SSH Keys", "*.pem *.key *.ppk"), ("All Files", "*.*")]
        )
        if file_path:
            self.key_file_entry.delete(0, tk.END)
            self.key_file_entry.insert(0, file_path)
