"""
SSH Client — главный файл запуска
"""

import tkinter as tk
from src.gui import SSHApp


def main():
    """Точка входа приложения"""
    root = tk.Tk()
    app = SSHApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
