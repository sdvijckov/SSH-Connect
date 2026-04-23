# 🐶 SSH Web Desktop — Файловый менеджер

Веб-интерфейс для навигации по файловой системе SSH-сервера. Часть проекта **"Собачья мудрость. Секрет счастья"**.

## Что это

Простой файловый менеджер в браузере:
- Навигация по папкам сервера
- Просмотр файлов и директорий
- Создание папок
- Всё через SSH

---

## Установка

### Требования
- **Python 3.10+** (https://python.org)
- **Git** (опционально)

### 1. Клонируй репозиторий
```bash
git clone https://github.com/your-username/ssh-connect.git
cd ssh-connect/web-desktop
```

### 2. Установи зависимости
```bash
pip install -r backend/requirements.txt
```

Если нет файла — установи вручную:
```bash
pip install fastapi uvicorn paramiko websockets python-multipart
```

### 3. Запусти сервер
```bash
cd backend
python main.py
```

Открой браузер: http://localhost:8000

---

## Запуск из SSH Connect

Если ты используешь **SSH Connect**, просто нажми кнопку **🌐 Веб-десктоп** — сервер запустится автоматически, браузер откроется с авто-подключением.

---

## Архитектура

```
web-desktop/
├── frontend/          # HTML/CSS/JS
│   ├── index.html     # Главная страница
│   ├── css/           # Стили
│   └── js/            # Скрипты (window-manager, file-manager)
│
├── backend/           # Python сервер
│   ├── main.py        # FastAPI сервер
│   ├── ssh_manager.py # SSH менеджер
│   ├── file_manager.py # Файловые операции (SFTP)
│   └── requirements.txt
```

### Как работает

1. **SSH Connect** подключается к серверу → сохраняет данные в URL
2. Пользователь нажимает **🌐 Веб-десктоп**
3. Запускается локальный сервер (FastAPI на порту 8000)
4. Открывается браузер → автоматическое подключение
5. Пользователь видит рабочий стол с файловым менеджером

---

## API

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/` | Главная страница |
| `POST` | `/api/connect` | SSH подключение |
| `POST` | `/api/files/list` | Список файлов |
| `POST` | `/api/files/read` | Чтение файла |
| `POST` | `/api/files/save` | Сохранение файла |
| `POST` | `/api/files/delete` | Удаление |
| `POST` | `/api/files/mkdir` | Создание папки |
| `POST` | `/api/files/rename` | Переименование |
| `POST` | `/api/disconnect` | Отключение |

---

## Технологии

- **Бэкенд:** Python, FastAPI, uvicorn, paramiko
- **Фронтенд:** HTML5, CSS3, Vanilla JS
- **Архитектура:** Одностраничное приложение с WebSocket терминалом

---

## Лицензия

Проект "Собачья мудрость. Секрет счастья" © 2026
