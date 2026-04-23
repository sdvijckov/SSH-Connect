# -*- coding: utf-8 -*-
"""
Move Cursor - Утилита для прокрутки консольных окон.

Быстрый запуск скрипта.
Для использования в качестве модуля импортируйте из src.main.
"""

import sys
import os

# Добавляем путь к src для импорта
script_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(script_dir, 'src')

# Проверка наличия папки src
if not os.path.isdir(src_path):
    print(f"ОШИБКА: Папка 'src' не найдена по пути: {src_path}")
    print(f"Убедитесь, что вы скопировали всю папку move_cursor целиком!")
    print(f"Текущая папка: {os.getcwd()}")
    print(f"Содержимое папки: {os.listdir(script_dir)}")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from main import main
except ImportError as e:
    print(f"ОШИБКА импорта: {e}")
    print(f"Путь к src: {src_path}")
    print(f"Содержимое src: {os.listdir(src_path)}")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

if __name__ == '__main__':
    main()
