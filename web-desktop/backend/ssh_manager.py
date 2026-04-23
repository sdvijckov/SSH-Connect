"""
SSH менеджер для веб-десктопа
Управляет SSH подключениями и выполнением команд
"""

import paramiko
import threading
import time
from typing import Optional


class SSHSession:
    """Одна SSH сессия с поддержкой интерактивного shell"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.client: Optional[paramiko.SSHClient] = None
        self.channel = None
        self.shell_thread: Optional[threading.Thread] = None
        self.running = False
        self.callbacks = []

    def connect(self, hostname: str, port: int, username: str,
                password: Optional[str] = None, key_file: Optional[str] = None) -> tuple[bool, str]:
        """Подключение к серверу"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if key_file:
                self.client.connect(
                    hostname=hostname, port=port, username=username,
                    key_filename=key_file, timeout=10
                )
            else:
                self.client.connect(
                    hostname=hostname, port=port, username=username,
                    password=password, timeout=10
                )

            # Открываем интерактивный shell
            self.channel = self.client.invoke_shell(
                term='xterm-256color',
                width=120,
                height=30
            )
            self.channel.settimeout(0)

            self.running = True
            self.shell_thread = threading.Thread(
                target=self._read_shell_output,
                daemon=True,
                name=f"shell-reader-{self.session_id}"
            )
            self.shell_thread.start()

            return True, "Подключено"

        except Exception as e:
            return False, str(e)

    def _read_shell_output(self):
        """Фоновое чтение вывода shell"""
        buffer = ""
        while self.running:
            try:
                if self.channel.recv_ready():
                    data = self.channel.recv(4096).decode('utf-8', errors='replace')
                    buffer += data

                    # Отправляем данные всем подписчикам
                    if buffer:
                        for callback in self.callbacks:
                            try:
                                callback(buffer)
                            except Exception:
                                pass
                        buffer = ""

                time.sleep(0.05)
            except Exception:
                time.sleep(0.1)

    def send_input(self, data: str):
        """Отправка ввода в shell"""
        if self.channel and self.channel.send_ready():
            self.channel.send(data)

    def add_callback(self, callback):
        """Добавить обработчик вывода"""
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        """Удалить обработчик"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def resize(self, width: int, height: int):
        """Изменить размер терминала"""
        if self.channel:
            self.channel.resize_pty(width=width, height=height)

    def close(self):
        """Закрыть сессию"""
        self.running = False
        if self.shell_thread:
            self.shell_thread.join(timeout=2)
        if self.channel:
            self.channel.close()
        if self.client:
            self.client.close()
