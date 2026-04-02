# ⌨️ Справочник команд Linux

## Быстрые команды в SSH Connect

Внизу программы — панель быстрых команд. Нажми чтобы скопировать!

| Кнопка | Команда | Описание |
|--------|---------|----------|
| 📊 **uptime** | `uptime` | Время работы, нагрузка |
| 💾 **df -h** | `df -h` | Место на диске |
| 📁 **ls -la** | `ls -la` | Список файлов |
| 🔝 **top** | `top -b -n 1` | Процессы |
| 🌡️ **free -h** | `free -h` | Память |
| 📦 **apt update** | `sudo apt update` | Обновление пакетов |
| 🐍 **python3** | `python3 --version` | Версия Python |
| 📝 **tail logs** | `tail -f /var/log/syslog` | Логи |

---

## Популярные команды Linux

### 📊 Информация о системе

```bash
# Время работы и нагрузка
uptime

# Версия ядра
uname -a

# Информация об ОС
cat /etc/os-release

# Загрузка процессора
top -b -n 1

# Температура CPU (если есть датчики)
sensors
```

---

### 💾 Дисковое пространство

```bash
# Свободное место
df -h

# Размер папки
du -sh /home/sheldon

# Большие файлы
find / -type f -size +100M

# Очистка кэша
sudo apt clean
```

---

### 📁 Файлы и папки

```bash
# Список файлов
ls -la

# Перейти в папку
cd /home/sheldon

# Создать папку
mkdir new_folder

# Удалить файл
rm filename.txt

# Удалить папку
rm -rf folder_name

# Копировать файл
cp file1.txt file2.txt

# Переместить файл
mv file1.txt /home/sheldon/

# Переименовать файл
mv old_name.txt new_name.txt

# Найти файл
find / -name "filename.txt"
```

---

### 🌐 Сеть

```bash
# IP адрес
ip addr show

# Открытые порты
netstat -tulpn

# Пинг
ping -c 4 google.com

# DNS
cat /etc/resolv.conf

# Шлюз
ip route show
```

---

### ⚙️ Процессы

```bash
# Список процессов
ps aux

# Процессы пользователя
ps -u root

# Убить процесс
kill <PID>

# Убить принудительно
kill -9 <PID>

# Найти процесс
ps aux | grep python

# Top (интерактивно)
top

# Htop (красивее)
htop
```

---

### 📝 Логи

```bash
# Просмотр логов
tail -f /var/log/syslog

# Последние 100 строк
tail -n 100 /var/log/syslog

# Поиск в логах
grep "error" /var/log/syslog

# Логи авторизации
tail -f /var/log/auth.log

# Журнал systemd
journalctl -f
```

---

### 🐍 Python

```bash
# Версия Python
python3 --version

# Запуск скрипта
python3 script.py

# Установка пакета
pip3 install package_name

# Список пакетов
pip3 list

# Обновить pip
pip3 install --upgrade pip

# Виртуальное окружение
python3 -m venv venv
source venv/bin/activate
```

---

### 📦 Установка пакетов (APT)

```bash
# Обновить список пакетов
sudo apt update

# Обновить установленные пакеты
sudo apt upgrade -y

# Установить пакет
sudo apt install package_name -y

# Удалить пакет
sudo apt remove package_name

# Поиск пакета
apt search package_name

# Информация о пакете
apt show package_name
```

---

### 🔐 Безопасность

```bash
# Блокировка экрана (в GUI)
xfce4-screensaver-command -l

# Смена пароля пользователя
passwd

# Добавить пользователя
sudo adduser username

# Добавить в sudo
sudo usermod -aG sudo username

# История команд
history

# Очистить историю
history -c
```

---

### 🔄 Перезагрузка и выключение

```bash
# Перезагрузка
sudo reboot

# Выключение
sudo shutdown now

# Выключение через 1 минуту
sudo shutdown +1

# Отменить выключение
sudo shutdown -c
```

---

### 🖥️ VNC (графический интерфейс)

```bash
# Запустить VNC
vncserver :1

# Остановить VNC
vncserver -kill :1

# Список сессий
vncserver -list

# Сменить пароль VNC
vncpasswd
```

---

## 🔍 Поиск команд

### Если забыл команду

```bash
# Поиск по описанию
apropos keyword

# Например
apropos network    # Всё про сеть
apropos disk       # Всё про диски
```

### Встроенная справка

```bash
# Мануал
man command

# Например
man ls
man grep

# Выход из man: q
```

---

## 📋 Шпаргалка для новичков

| Что хочу сделать | Команда |
|------------------|---------|
| "Где я?" | `pwd` |
| "Что тут?" | `ls -la` |
| "Как выйти?" | `exit` |
| "Помогите!" | `man command` |
| "Обновить систему" | `sudo apt update && sudo apt upgrade -y` |
| "Перезагрузить" | `sudo reboot` |

---

**См. также:**
- [Установка](INSTALL.md)
- [Использование](USAGE.md)
- [Настройка GUI](GUI_SETUP.md)
