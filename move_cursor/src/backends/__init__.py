# -*- coding: utf-8 -*-
"""
Бэкенды для различных операционных систем.
"""

# Импорты работают и как пакет, и как скрипт
try:
    from .base import BaseBackend
except ImportError:
    from base import BaseBackend

__all__ = ['BaseBackend', 'get_backend']


def get_backend():
    """
    Автоматически определяет и возвращает бэкенд для текущей ОС.
    
    Returns:
        BaseBackend: Экземпляр бэкенда для текущей ОС.
    
    Raises:
        ImportError: Если ОС не поддерживается или нет зависимостей.
    """
    import sys
    
    if sys.platform == 'win32':
        from .windows import WindowsBackend
        return WindowsBackend()
    
    elif sys.platform == 'linux':
        from .linux import LinuxBackend
        return LinuxBackend()
    
    elif sys.platform == 'darwin':
        from .darwin import DarwinBackend
        return DarwinBackend()
    
    else:
        raise ImportError(f"Неподдерживаемая операционная система: {sys.platform}")
