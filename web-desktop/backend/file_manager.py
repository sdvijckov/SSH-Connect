"""
Файловый менеджер для веб-десктопа
Операции с файлами через SFTP
"""

import os
from typing import Optional


class FileManager:
    """Управление файлами на сервере через SFTP"""

    def __init__(self, ssh_session):
        """Принимает подключённый paramiko SSH client"""
        self.ssh_client = ssh_session.client

    def list_directory(self, path: str = "/") -> tuple[bool, list[dict], str]:
        """Список файлов и папок"""
        try:
            sftp = self.ssh_client.open_sftp()
            entries = []

            for entry in sftp.listdir_attr(path):
                is_dir = self._is_dir(entry)
                entries.append({
                    "name": entry.filename,
                    "is_dir": is_dir,
                    "size": entry.st_size if not is_dir else 0,
                    "modified": entry.st_mtime,
                    "permissions": entry.st_mode
                })

            # Сортировка: папки primero, затем по имени
            entries.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            sftp.close()

            return True, entries, ""

        except Exception as e:
            return False, [], str(e)

    def read_file(self, path: str, max_size: int = 1024 * 1024) -> tuple[bool, str, str]:
        """Чтение текстового файла"""
        try:
            sftp = self.ssh_client.open_sftp()

            # Проверяем размер
            file_attr = sftp.stat(path)
            if file_attr.st_size > max_size:
                sftp.close()
                return False, "", f"Файл слишком большой ({file_attr.st_size / 1024:.0f} KB)"

            with sftp.open(path, 'r') as f:
                content = f.read()

            sftp.close()
            return True, content, ""

        except Exception as e:
            return False, "", str(e)

    def save_file(self, path: str, content: str) -> tuple[bool, str]:
        """Сохранение файла"""
        try:
            sftp = self.ssh_client.open_sftp()
            with sftp.open(path, 'w') as f:
                f.write(content)
            sftp.close()
            return True, "Сохранено"

        except Exception as e:
            return False, str(e)

    def delete(self, path: str) -> tuple[bool, str]:
        """Удаление файла или папки"""
        try:
            sftp = self.ssh_client.open_sftp()

            # Проверяем, папка или файл
            try:
                sftp.stat(path + "/")
                # Это папка — удаляем рекурсивно
                self._rmtree(sftp, path)
            except IOError:
                # Это файл
                sftp.remove(path)

            sftp.close()
            return True, "Удалено"

        except Exception as e:
            return False, str(e)

    def rename(self, old_path: str, new_path: str) -> tuple[bool, str]:
        """Переименование"""
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.rename(old_path, new_path)
            sftp.close()
            return True, "Переименовано"
        except Exception as e:
            return False, str(e)

    def mkdir(self, path: str) -> tuple[bool, str]:
        """Создание папки"""
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.mkdir(path)
            sftp.close()
            return True, "Папка созданана"
        except Exception as e:
            return False, str(e)

    def download_info(self, path: str) -> tuple[bool, dict, str]:
        """Информация о файле"""
        try:
            sftp = self.ssh_client.open_sftp()
            attr = sftp.stat(path)
            info = {
                "name": os.path.basename(path),
                "size": attr.st_size,
                "modified": attr.st_mtime,
                "permissions": attr.st_mode,
                "is_dir": self._is_dir(attr)
            }
            sftp.close()
            return True, info, ""
        except Exception as e:
            return False, {}, str(e)

    def _is_dir(self, attr) -> bool:
        """Проверка, является ли запись директорией"""
        import stat
        return stat.S_ISDIR(attr.st_mode)

    def _rmtree(self, sftp, path: str):
        """Рекурсивное удаление папки"""
        for entry in sftp.listdir_attr(path):
            entry_path = f"{path}/{entry.filename}"
            if self._is_dir(entry):
                self._rmtree(sftp, entry_path)
            else:
                sftp.remove(entry_path)
        sftp.rmdir(path)
