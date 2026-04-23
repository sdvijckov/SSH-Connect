# -*- coding: utf-8 -*-
"""
macOS-бэкенд для утилиты Move Cursor.
Использует Quartz/CoreGraphics для работы с окнами.

ТРЕБУЕТСЯ РЕАЛИЗАЦИЯ:
- Установка pyobjc: pip install pyobjc-core pyobjc-framework-Quartz
"""

import logging
from typing import List, Optional

from .base import BaseBackend

logger = logging.getLogger(__name__)


class DarwinBackend(BaseBackend):
    """
    Бэкенд для операционной системы macOS.
    
    Требует реализации! Использует Quartz/CoreGraphics для работы с окнами.
    """
    
    # Терминалы macOS
    MACOS_TERMINAL_BUNDLES = [
        "com.apple.Terminal",        # Terminal.app
        "com.googlecode.iterm2",     # iTerm2
        "com.microsoft.VSCode",      # VS Code
        "com.jetbrains.pycharm",     # PyCharm
        "com.jetbrains.intellij",    # IntelliJ IDEA
        "org.alacritty",             # Alacritty
        "net.kovidgoyal.kitty",      # Kitty
    ]
    
    def __init__(self):
        """Инициализация macOS-бэкенда."""
        super().__init__()
        self._init_quartz()
    
    def _init_quartz(self) -> None:
        """Инициализирует фреймворк Quartz."""
        try:
            import Quartz
            logger.info("Quartz фреймворк инициализирован")
        except ImportError:
            logger.error("Требуется pyobjc: pip install pyobjc-core pyobjc-framework-Quartz")
            raise
    
    def get_terminal_window_classes(self) -> List[str]:
        """Возвращает список bundle ID macOS-терминалов."""
        return self.MACOS_TERMINAL_BUNDLES.copy()
    
    def get_active_window_class(self) -> Optional[str]:
        """
        Получает bundle ID активного приложения через Quartz.
        
        TODO: Реализовать через CGWindowListCopyWindowInfo
        """
        logger.warning("macOS-бэкенд требует реализации")
        return None
    
    def is_terminal_window(self, bundle_id: str) -> bool:
        """Проверяет, является ли приложение терминалом."""
        if not bundle_id:
            return False
        return bundle_id.lower() in [b.lower() for b in self.get_terminal_window_classes()]
    
    def scroll_vertical(self, hwnd: int, direction: str, amount: int = 0) -> bool:
        """
        Выполняет вертикальную прокрутку.
        
        TODO: Реализовать через CGEventCreateScrollWheelEvent
        """
        logger.warning("macOS-бэкенд требует реализации")
        return False
    
    def scroll_horizontal(self, hwnd: int, direction: str, amount: int = 0) -> bool:
        """
        Выполняет горизонтальную прокрутку.
        
        TODO: Реализовать
        """
        logger.warning("macOS-бэкенд требует реализации")
        return False
    
    def show_notification(self, title: str, message: str) -> None:
        """
        Показывает уведомление через NSUserNotification.
        
        TODO: Реализовать через Cocoa/PyObjC
        """
        logger.warning("macOS-бэкенд требует реализации")
        pass
    
    def get_active_window_handle(self) -> int:
        """
        Получает CGWindowID активного окна.
        
        TODO: Реализовать
        """
        logger.warning("macOS-бэкенд требует реализации")
        return 0
