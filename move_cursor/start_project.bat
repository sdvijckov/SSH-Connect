@echo off
REM ============================================
REM Move Cursor Launcher
REM Запуск утилиты прокрутки + проекта
REM ============================================

REM Путь к утилите Move Cursor
set MOVE_CURSOR_PATH=D:\Projects python\Help\move_cursor\move_cursor.py

REM Запуск утилиты прокрутки в отдельном окне (свёрнутым /min)
start /min "Move Cursor" python "%MOVE_CURSOR_PATH%"

REM Небольшая пауза (2 секунды) чтобы утилита успела запуститься
timeout /t 2 /nobreak >nul

REM Запуск проекта в cmd
start "" cmd /k "qwen --continue"
