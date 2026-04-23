# -*- coding: utf-8 -*-
"""
Главный модуль утилиты Move Cursor.
Управляет перехватом клавиш и прокруткой окон.
"""

import logging
import sys
from typing import Optional

from pynput import keyboard

# Импорты работают и как пакет, и как скрипт
try:
    from .config import (
        LOG_LEVEL,
        LOG_FILE,
        PAUSE_KEY,
        SCROLL_UP_KEY,
        SCROLL_DOWN_KEY,
        HORIZONTAL_SCROLL_ENABLED,
        SHOW_PAUSE_NOTIFICATION,
        SCROLL_TYPE,
        SCROLL_LINES,
        SCROLL_COLUMNS,
    )
    from .backends import get_backend
    from .backends.base import BaseBackend
except ImportError:
    from config import (
        LOG_LEVEL,
        LOG_FILE,
        PAUSE_KEY,
        SCROLL_UP_KEY,
        SCROLL_DOWN_KEY,
        HORIZONTAL_SCROLL_ENABLED,
        SHOW_PAUSE_NOTIFICATION,
        SCROLL_TYPE,
        SCROLL_LINES,
        SCROLL_COLUMNS,
    )
    from backends import get_backend
    from backends.base import BaseBackend

logger = logging.getLogger(__name__)


class ScrollController:
    """
    Контроллер прокрутки.
    
    Управляет перехватом клавиш, прокруткой окон и состоянием паузы.
    """
    
    # Маппинг названий клавиш из конфига в объекты pynput
    KEY_MAP = {
        'page_up': keyboard.Key.page_up,
        'page_down': keyboard.Key.page_down,
        'home': keyboard.Key.home,
        'end': keyboard.Key.end,
        'up': keyboard.Key.up,
        'down': keyboard.Key.down,
        'f12': keyboard.Key.f12,
        'scroll_lock': keyboard.Key.scroll_lock,
        'pause': keyboard.Key.pause,
        'esc': keyboard.Key.esc,
    }
    
    def __init__(self):
        """Инициализация контроллера."""
        self._backend: BaseBackend = get_backend()
        self._listener: Optional[keyboard.Listener] = None
        self._is_running = False
        
        # Состояния
        self._shift_pressed = False
        
        # Получаем клавиши из конфига
        self._pause_key = self._get_key_from_config(PAUSE_KEY)
        self._scroll_up_key = self._get_key_from_config(SCROLL_UP_KEY)
        self._scroll_down_key = self._get_key_from_config(SCROLL_DOWN_KEY)
        
        # Настройка логирования
        self._setup_logging()
    
    def _get_key_from_config(self, key_name: str):
        """
        Преобразует название клавиши из конфига в объект pynput.
        
        Args:
            key_name (str): Название клавиши из конфига.
        
        Returns:
            Объект pynput.keyboard.Key или None.
        """
        if key_name == 'none' or not key_name:
            return None
        return self.KEY_MAP.get(key_name.lower())
    
    def _setup_logging(self) -> None:
        """Настраивает логирование в консоль."""
        log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        
        # Создаём logger
        logger.setLevel(log_level)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    def _is_scroll_key(self, key) -> bool:
        """Проверяет, является ли клавиша клавишей прокрутки."""
        return key in (self._scroll_up_key, self._scroll_down_key)
    
    def _handle_scroll(self, direction: str) -> None:
        """
        Обрабатывает прокрутку активного окна.
        
        Args:
            direction (str): Направление прокрутки ('up' или 'down').
        """
        if self._backend.is_paused:
            return
        
        window_class = self._backend.get_active_window_class()
        
        if not window_class:
            logger.debug("Не удалось определить класс активного окна")
            return
        
        if not self._backend.is_terminal_window(window_class):
            logger.debug(f"Окно не является терминалом: {window_class}")
            return
        
        hwnd = self._backend.get_active_window_handle() if hasattr(self._backend, 'get_active_window_handle') else 0
        
        # Горизонтальная прокрутка с Shift
        if self._shift_pressed and HORIZONTAL_SCROLL_ENABLED:
            h_direction = 'left' if direction == 'up' else 'right'
            success = self._backend.scroll_horizontal(hwnd, h_direction)
            logger.info(f"Горизонтальная прокрутка: {h_direction} ({window_class})")
        else:
            success = self._backend.scroll_vertical(hwnd, direction)
            logger.info(f"Вертикальная прокрутка: {direction} ({window_class})")
        
        if not success:
            logger.warning(f"Не удалось выполнить прокрутку: {direction}")
    
    def _show_pause_notification(self, is_paused: bool) -> None:
        """Показывает уведомление о состоянии паузы."""
        if SHOW_PAUSE_NOTIFICATION and hasattr(self._backend, 'show_notification'):
            title = "Move Cursor"
            message = "Перехват ПАУЗА" if is_paused else "Перехват АКТИВЕН"
            self._backend.show_notification(title, message)
    
    def on_press(self, key) -> None:
        """
        Обработчик нажатия клавиш.
        
        Args:
            key: Объект клавиши pynput.
        """
        try:
            # Отслеживаем Shift для горизонтальной прокрутки
            if key == keyboard.Key.shift:
                self._shift_pressed = True
                return
            
            # Пауза
            if key == self._pause_key:
                new_state = self._backend.toggle_pause()
                self._show_pause_notification(new_state)
                logger.info(f"Пауза: {'ВКЛ' if new_state else 'ВЫКЛ'}")
                return
            
            # Прокрутка
            if self._is_scroll_key(key):
                if key == self._scroll_up_key:
                    self._handle_scroll('up')
                elif key == self._scroll_down_key:
                    self._handle_scroll('down')
        
        except Exception as e:
            logger.error(f"Ошибка в on_press: {e}", exc_info=True)
    
    def on_release(self, key) -> None:
        """
        Обработчик отпускания клавиш.
        
        Args:
            key: Объект клавиши pynput.
        """
        try:
            if key == keyboard.Key.shift:
                self._shift_pressed = False
        
        except Exception as e:
            logger.error(f"Ошибка в on_release: {e}", exc_info=True)
    
    def start(self) -> None:
        """Запускает контроллер прокрутки."""
        if self._is_running:
            logger.warning("Контроллер уже запущен")
            return
        
        logger.info("=" * 50)
        logger.info("Move Cursor - Утилита для прокрутки терминалов")
        logger.info("=" * 50)
        logger.info(f"Бэкенд: {self._backend.__class__.__name__}")
        logger.info(f"Клавиша паузы: {PAUSE_KEY}")
        logger.info(f"Прокрутка вверх: {SCROLL_UP_KEY}")
        logger.info(f"Прокрутка вниз: {SCROLL_DOWN_KEY}")
        logger.info(f"Тип прокрутки: {SCROLL_TYPE}")
        if SCROLL_TYPE == 'line':
            logger.info(f"Строк за нажатие: {SCROLL_LINES}")
            logger.info(f"Колонок за нажатие: {SCROLL_COLUMNS}")
        logger.info(f"Горизонтальная прокрутка: {'ВКЛ' if HORIZONTAL_SCROLL_ENABLED else 'ВЫКЛ'} (Shift + клавиша)")
        logger.info("=" * 50)
        
        try:
            self._backend.start()
            self._is_running = True
            
            # Запускаем слушателя клавиатуры
            with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            ) as self._listener:
                logger.info("Слушатель клавиатуры запущен. Нажмите ESC для выхода.")
                self._listener.join()
        
        except Exception as e:
            logger.critical(f"Критическая ошибка: {e}", exc_info=True)
            raise
        
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Останавливает контроллер прокрутки."""
        if not self._is_running:
            return
        
        logger.info("Остановка контроллера...")
        self._is_running = False
        self._backend.stop()
        
        if self._listener:
            self._listener.stop()
        
        logger.info("Контроллер остановлен")


def main():
    """Точка входа приложения."""
    controller = ScrollController()
    controller.start()


if __name__ == '__main__':
    main()
