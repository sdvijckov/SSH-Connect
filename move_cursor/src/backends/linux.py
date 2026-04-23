# -*- coding: utf-8 -*-
"""
Linux-бэкенд для утилиты Move Cursor.
Использует X11 (python-xlib) для работы с окнами.

ТРЕБУЕТСЯ РЕАЛИЗАЦИЯ:
- Установка python-xlib: pip install python-xlib
- Установка Xlib: sudo apt-get install python3-xlib (или аналог)
"""

import logging
from typing import List, Optional

from .base import BaseBackend

logger = logging.getLogger(__name__)


class LinuxBackend(BaseBackend):
    """
    Бэкенд для операционной системы Linux.
    
    Требует реализации! Использует X11 для работы с окнами.
    """
    
    # Терминалы Linux
    LINUX_TERMINAL_CLASSES = [
        "gnome-terminal",      # GNOME Terminal
        "konsole",             # Konsole
        "xterm",               # XTerm
        "urxvt",               # URxvt
        "alacritty",           # Alacritty
        "kitty",               # Kitty
        "terminator",          # Terminator
        "guake",               # Guake
        "xfce4-terminal",      # XFCE Terminal
    ]
    
    def __init__(self):
        """Инициализация Linux-бэкенда."""
        super().__init__()
        self._display = None
        self._init_x11()
    
    def _init_x11(self) -> None:
        """Инициализирует соединение с X-сервером."""
        try:
            from Xlib import X, display
            self._display = display.Display()
            logger.info("X11 соединение установлено")
        except ImportError:
            logger.error("Требуется python-xlib: pip install python-xlib")
            raise
        except Exception as e:
            logger.error(f"Не удалось подключиться к X-серверу: {e}")
            raise
    
    def get_terminal_window_classes(self) -> List[str]:
        """Возвращает список классов окон Linux-терминалов."""
        return self.LINUX_TERMINAL_CLASSES.copy()
    
    def get_active_window_class(self) -> Optional[str]:
        """
        Получает класс активного окна через X11.
        
        TODO: Реализовать получение активного окна через _NET_ACTIVE_WINDOW
        """
        logger.warning("Linux-бэкенд требует реализации")
        return None
    
    def is_terminal_window(self, window_class: str) -> bool:
        """Проверяет, является ли окно терминалом."""
        if not window_class:
            return False
        return window_class.lower() in [c.lower() for c in self.get_terminal_window_classes()]
    
    def scroll_vertical(self, hwnd: int, direction: str, amount: int = 0) -> bool:
        """
        Выполняет вертикальную прокрутку.
        
        TODO: Реализовать через XTestFakeButtonEvent или XTestFakeMotionEvent
        """
        logger.warning("Linux-бэкенд требует реализации")
        return False
    
    def scroll_horizontal(self, hwnd: int, direction: str, amount: int = 0) -> bool:
        """
        Выполняет горизонтальную прокрутку.
        
        TODO: Реализовать
        """
        logger.warning("Linux-бэкенд требует реализации")
        return False
    
    def show_notification(self, title: str, message: str) -> None:
        """
        Показывает уведомление через notify-send.
        
        TODO: Реализовать через dbus или subprocess
        """
        logger.warning("Linux-бэкенд требует реализации")
        pass
    
    def __del__(self):
        """Закрывает соединение с X-сервером."""
        if self._display:
            try:
                self._display.close()
            except Exception:
                pass
