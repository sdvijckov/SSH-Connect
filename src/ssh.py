"""
SSH модуль — простая логика подключения
"""

import paramiko
from typing import Optional, Tuple, List


class SSHClient:
    """Класс для управления SSH соединением"""

    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp = None
        self.is_connected = False

    def connect(
        self,
        hostname: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        key_file: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Подключение к серверу"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if key_file:
                self.client.connect(
                    hostname=hostname,
                    port=port,
                    username=username,
                    key_filename=key_file,
                    timeout=10,
                    allow_agent=True
                )
            else:
                self.client.connect(
                    hostname=hostname,
                    port=port,
                    username=username,
                    password=password,
                    timeout=10
                )

            self.sftp = self.client.open_sftp()
            self.is_connected = True
            return True, "Подключение успешно!"

        except Exception as e:
            return False, str(e)

    def execute_command(self, command: str) -> Tuple[bool, str]:
        """Выполнение команды"""
        if not self.is_connected or not self.client:
            return False, "Нет подключения"

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0 and error:
                return False, error
            return True, output if output else error

        except Exception as e:
            return False, str(e)

    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """Загрузка файла на сервер"""
        if not self.is_connected:
            return False, "Нет подключения"

        try:
            self.sftp.put(local_path, remote_path)
            return True, f"Файл загружен: {remote_path}"
        except Exception as e:
            return False, str(e)

    def download_file(self, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """Скачивание файла с сервера"""
        if not self.is_connected:
            return False, "Нет подключения"

        try:
            self.sftp.get(remote_path, local_path)
            return True, f"Файл скачан: {local_path}"
        except Exception as e:
            return False, str(e)

    def list_directory(self, path: str = '.') -> Tuple[bool, List[str]]:
        """Список файлов в директории"""
        if not self.is_connected:
            return False, []

        try:
            files = self.sftp.listdir(path)
            return True, files
        except Exception as e:
            return False, []

    def disconnect(self) -> Tuple[bool, str]:
        """Отключение от сервера"""
        try:
            if self.sftp:
                self.sftp.close()
            if self.client:
                self.client.close()
            self.is_connected = False
            return True, "Отключено"
        except Exception as e:
            return False, str(e)
