# -*- coding: utf-8 -*-
"""
Windows-бэкенд для утилиты Move Cursor.
Использует pywin32 для работы с окнами и сообщениями Windows.
"""

import logging
import ctypes
from typing import List, Optional

import win32api
import win32con
import win32gui

from .base import BaseBackend

logger = logging.getLogger(__name__)


class WindowsBackend(BaseBackend):
    """
    Бэкенд для операционной системы Windows.
    
    Использует Win32 API для получения информации об окнах
    и отправки сообщений прокрутки.
    """
    
    # Сообщения для прокрутки
    WM_VSCROLL = win32con.WM_VSCROLL
    WM_HSCROLL = win32con.WM_HSCROLL
    
    def __init__(self):
        """Инициализация Windows-бэкенда."""
        super().__init__()
        self._terminal_classes: List[str] = []
    
    def get_terminal_window_classes(self) -> List[str]:
        """
        Возвращает список классов окон, которые считаются терминалами.
        
        Returns:
            List[str]: Список имён классов окон.
        """
        # Импорты работают и как пакет, и как скрипт
        try:
            from ..config import WINDOWS_TERMINAL_CLASSES
        except ImportError:
            from config import WINDOWS_TERMINAL_CLASSES
        return WINDOWS_TERMINAL_CLASSES.copy()
    
    def get_active_window_class(self) -> Optional[str]:
        """
        Получает класс активного окна.
        
        Returns:
            Optional[str]: Класс активного окна или None, если не удалось определить.
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                return win32gui.GetClassName(hwnd)
        except Exception as e:
            logger.debug(f"Не удалось получить класс активного окна: {e}")
        return None
    
    def is_terminal_window(self, window_class: str) -> bool:
        """
        Проверяет, является ли окно терминалом.
        
        Args:
            window_class (str): Класс окна для проверки.
        
        Returns:
            bool: True, если окно является терминалом.
        """
        if not window_class:
            return False
        
        # Точное совпадение
        if window_class in self.get_terminal_window_classes():
            return True
        
        # Частичное совпадение (для некоторых терминалов)
        window_class_lower = window_class.lower()
        for terminal_class in self.get_terminal_window_classes():
            if terminal_class.lower() in window_class_lower:
                return True
        
        return False
    
    def scroll_vertical(self, hwnd: int, direction: str, amount: int = 0) -> bool:
        """
        Выполняет вертикальную прокрутку окна.
        
        Args:
            hwnd (int): Handle окна.
            direction (str): Направление прокрутки ('up' или 'down').
            amount (int): Количество строк (для построчной прокрутки).
        
        Returns:
            bool: True, если прокрутка успешна.
        """
        if not hwnd:
            return False
        
        # Импортируем настройки
        try:
            from ..config import SCROLL_TYPE, SCROLL_LINES
        except ImportError:
            from config import SCROLL_TYPE, SCROLL_LINES
        
        # Выбираем команду в зависимости от типа прокрутки
        if SCROLL_TYPE == 'line':
            command = win32con.SB_LINEUP if direction == 'up' else win32con.SB_LINEDOWN
            # Для построчной прокрутки отправляем сообщение несколько раз
            lines_to_scroll = amount if amount > 0 else SCROLL_LINES
            try:
                if not win32gui.IsWindow(hwnd):
                    logger.debug(f"Окно {hwnd} не существует")
                    return False
                
                for _ in range(lines_to_scroll):
                    win32api.PostMessage(hwnd, self.WM_VSCROLL, command, 0)
                logger.debug(f"Вертикальная прокрутка (lines): {direction} x{lines_to_scroll} для окна {hwnd}")
                return True
            except Exception as e:
                logger.error(f"Ошибка при вертикальной прокрутке (lines): {e}")
                return False
        else:
            # Постраничная прокрутка
            command = win32con.SB_PAGEUP if direction == 'up' else win32con.SB_PAGEDOWN
            try:
                if not win32gui.IsWindow(hwnd):
                    logger.debug(f"Окно {hwnd} не существует")
                    return False
                
                win32api.PostMessage(hwnd, self.WM_VSCROLL, command, 0)
                logger.debug(f"Вертикальная прокрутка (page): {direction} для окна {hwnd}")
                return True
            except Exception as e:
                logger.error(f"Ошибка при вертикальной прокрутке (page): {e}")
                return False
    
    def scroll_horizontal(self, hwnd: int, direction: str, amount: int = 0) -> bool:
        """
        Выполняет горизонтальную прокрутку окна.
        
        Args:
            hwnd (int): Handle окна.
            direction (str): Направление ('left' или 'right').
            amount (int): Количество колонок.
        
        Returns:
            bool: True, если прокрутка успешна.
        """
        if not hwnd:
            return False
        
        # Импортируем настройки
        try:
            from ..config import SCROLL_COLUMNS
        except ImportError:
            from config import SCROLL_COLUMNS
        
        command = win32con.SB_LINELEFT if direction == 'left' else win32con.SB_LINERIGHT
        cols_to_scroll = amount if amount > 0 else SCROLL_COLUMNS
        
        try:
            if not win32gui.IsWindow(hwnd):
                logger.debug(f"Окно {hwnd} не существует")
                return False
            
            for _ in range(cols_to_scroll):
                win32api.PostMessage(hwnd, self.WM_HSCROLL, command, 0)
            
            logger.debug(f"Горизонтальная прокрутка: {direction} x{cols_to_scroll} для окна {hwnd}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при горизонтальной прокрутке: {e}")
            return False
    
    def show_notification(self, title: str, message: str) -> None:
        """
        Показывает пользователю уведомление через MessageBox.
        
        Args:
            title (str): Заголовок уведомления.
            message (str): Текст уведомления.
        """
        try:
            # MB_OK = 0x0, MB_ICONINFORMATION = 0x40, MB_TOPMOST = 0x40000
            ctypes.windll.user32.MessageBoxW(
                0, 
                message, 
                title, 
                0x0 | 0x40 | 0x40000
            )
            logger.debug(f"Показано уведомление: {title}")
        except Exception as e:
            logger.error(f"Не удалось показать уведомление: {e}")
    
    def get_active_window_handle(self) -> int:
        """
        Получает handle активного окна.
        
        Returns:
            int: Handle активного окна или 0, если не удалось определить.
        """
        try:
            return win32gui.GetForegroundWindow()
        except Exception as e:
            logger.debug(f"Не удалось получить handle активного окна: {e}")
            return 0
    
    def validate_window_handle(self, hwnd: int) -> bool:
        """
        Проверяет валидность handle окна.
        
        Args:
            hwnd (int): Handle для проверки.
        
        Returns:
            bool: True, если handle валиден.
        """
        try:
            return win32gui.IsWindow(hwnd)
        except Exception:
            return False
