# 🛠️ Установка и запуск

## 1. Требования

| Компонент | Требование |
|-----------|------------|
| **ОС** | Windows 10/11 |
| **Python** | 3.10 или выше |
| **Память** | 512 МБ RAM |
| **Место** | 100 МБ на диске |

---

## 2. Установка зависимостей

### Шаг 1: Проверка Python

```bash
python --version
```

Должно быть **Python 3.10** или выше.

---

### Шаг 2: Установка библиотек

```bash
pip install -r requirements_ssh.txt
```

**Устанавливаются:**
- `paramiko` — SSH библиотека
- `pyinstaller` — сборка в EXE
- `cryptography` — шифрование паролей

---

## 3. Установка дополнительных программ

### Kitty (SSH терминал)

**Kitty** — форк PuTTY с расширенными возможностями.

1. Скачай: https://www.9bis.net/kitty/
2. Скачай `kitty.exe` (portable версия)
3. Помести в папку проекта:
   ```
   D:\Projects python\SSH Connect\kitty.exe
   ```

**Преимущества Kitty перед PuTTY:**
- ✅ Поддержка пароля в командной строке (`-pw`)
- ✅ Сохранение сессий
- ✅ Встроенный SFTP
- ✅ Скрипты и автоматизация

---

### VNC Viewer (графический интерфейс)

**RealVNC Viewer** — клиент для подключения к VNC.

1. Скачай: https://www.realvnc.com/en/connect/download/viewer/
2. Установи или скачай portable версию
3. Помести `vncviewer.exe` в папку проекта:
   ```
   D:\Projects python\SSH Connect\vncviewer.exe
   ```

---

## 4. Запуск программы

### Вариант 1: Через командную строку

```bash
cd D:\Projects python\SSH Connect
python main.py
```

### Вариант 2: Через ssh_client.py

```bash
python ssh_client.py
```

### Вариант 3: Через файл

Дважды кликни на `main.py` или `ssh_client.py`

---

## 5. Проверка установки

### Проверка Python и библиотек

```bash
# Проверка Python
python --version

# Проверка paramiko
python -c "import paramiko; print(paramiko.__version__)"

# Проверка cryptography
python -c "import cryptography; print(cryptography.__version__)"
```

### Проверка Kitty

```bash
# Должно открыться окно Kitty
kitty.exe
```

### Проверка VNC Viewer

```bash
# Должно открыться окно VNC Viewer
vncviewer.exe
```

---

## 6. Сборка в EXE (опционально)

```bash
pyinstaller --onefile --windowed --name "SSH Connect" main.py
```

**После сборки:**
- EXE файл будет в папке `dist/`
- Скопируй `kitty.exe` и `vncviewer.exe` в папку с EXE

---

## 7. Первое использование

1. **Запусти** `python main.py`
2. **Введи данные** VPS (хост, логин, пароль)
3. **Нажми** "🔗 Подключиться"
4. **Kitty откроется** автоматически (свёрнутым)
5. **Для GUI** нажми "🖥️ Открыть GUI"

---

**См. также:**
- [Использование](USAGE.md)
- [Настройка GUI](GUI_SETUP.md)
- [Решение проблем](ISSUES.md)
