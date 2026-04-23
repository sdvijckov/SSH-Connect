# -*- coding: utf-8 -*-
"""
Базовый класс для всех бэкендов.
Определяет интерфейс, который должны реализовывать все платформы.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseBackend(ABC):
    """
    Абстрактный базовый класс для бэкендов.
    
    Все платформо-специфичные реализации должны наследоваться от этого класса.
    """
    
    def __init__(self):
        """Инициализация бэкенда."""
        self._is_running = False
        self._is_paused = False
    
    @property
    def is_running(self) -> bool:
        """Возвращает True, если бэкенд запущен."""
        return self._is_running
    
    @property
    def is_paused(self) -> bool:
        """Возвращает True, если перехват на паузе."""
        return self._is_paused
    
    @abstractmethod
    def get_terminal_window_classes(self) -> List[str]:
        """
        Возвращает список классов окон, которые считаются терминалами.
        
        Returns:
            List[str]: Список имён классов окон.
        """
        pass
    
    @abstractmethod
    def get_active_window_class(self) -> Optional[str]:
        """
        Получает класс активного окна.
        
        Returns:
            Optional[str]: Класс активного окна или None, если не удалось определить.
        """
        pass
    
    @abstractmethod
    def is_terminal_window(self, window_class: str) -> bool:
        """
        Проверяет, является ли окно терминалом.
        
        Args:
            window_class (str): Класс окна для проверки.
        
        Returns:
            bool: True, если окно является терминалом.
        """
        pass
    
    @abstractmethod
    def scroll_vertical(self, hwnd: int, direction: str, amount: int = 0) -> bool:
        """
        Выполняет вертикальную прокрутку окна.
        
        Args:
            hwnd (int): Handle окна (или идентификатор, специфичный для платформы).
            direction (str): Направление прокрутки ('up' или 'down').
            amount (int): Количество строк или страниц (зависит от реализации).
        
        Returns:
            bool: True, если прокрутка успешна.
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def show_notification(self, title: str, message: str) -> None:
        """
        Показывает пользователю уведомление.
        
        Args:
            title (str): Заголовок уведомления.
            message (str): Текст уведомления.
        """
        pass
    
    def start(self) -> None:
        """Запускает бэкенд."""
        self._is_running = True
        self._is_paused = False
    
    def stop(self) -> None:
        """Останавливает бэкенд."""
        self._is_running = False
        self._is_paused = False
    
    def toggle_pause(self) -> bool:
        """
        Переключает состояние паузы.
        
        Returns:
            bool: Новое состояние паузы.
        """
        self._is_paused = not self._is_paused
        return self._is_paused
    
    def set_pause(self, paused: bool) -> None:
        """
        Устанавливает состояние паузы.
        
        Args:
            paused (bool): True для включения паузы, False для выключения.
        """
        self._is_paused = paused
