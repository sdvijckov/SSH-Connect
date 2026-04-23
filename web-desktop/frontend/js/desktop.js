/**
 * Desktop — файловый менеджер на весь экран
 */

class Desktop {
    constructor() {
        this.sessionId = null;
        this.connected = false;

        this._initClock();
        this._initQuotes();
        this._initContextMenu();
        this._checkUrlParams();
    }

    /**
     * Проверка URL параметров для авто-подключения
     */
    async _checkUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const encoded = params.get('c');

        if (!encoded) {
            document.getElementById('status-text').textContent = 'Нет подключения — откройте из SSH Connect';
            return;
        }

        try {
            const json = decodeURIComponent(escape(atob(encoded)));
            const data = JSON.parse(json);

            const result = await fetch('/api/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    hostname: data.h,
                    port: data.p,
                    username: data.u,
                    password: data.w || undefined,
                    key_file: undefined
                })
            });

            const resultData = await result.json();

            if (resultData.success) {
                this.sessionId = resultData.session_id;
                this.connected = true;
                window.history.replaceState({}, '', '/');
                // Инициализируем файловый менеджер
                fileManagerApp.init(this.sessionId);
            } else {
                document.getElementById('status-text').textContent = 'Ошибка подключения: ' + resultData.message;
            }
        } catch (err) {
            console.error('Ошибка:', err);
            document.getElementById('status-text').textContent = 'Ошибка подключения';
        }
    }

    /**
     * Цитаты Шелдона в статус-баре (без авторства — только сама мысль)
     */
    _initQuotes() {
        const quotes = [
            "Счастье не имеет материального воплощения",
            "Жизнь иногда даёт нам пощёчины, но она делает это любя",
            "Если чувствуешь себя несчастным, постарайся сделать что-то хорошее миру",
            "Если не выйдешь из прошлого, не войдёшь в будущее",
            "Чем дольше цепляешься за прошлое, тем сложнее двигаться в будущее",
        ];

        const quoteEl = document.getElementById('status-quote');
        let currentIndex = 0;

        // Показываем первую цитату
        quoteEl.textContent = quotes[0];

        // Меняем каждые 12 секунд
        setInterval(() => {
            currentIndex = (currentIndex + 1) % quotes.length;
            quoteEl.style.opacity = '0';
            setTimeout(() => {
                quoteEl.textContent = quotes[currentIndex];
                quoteEl.style.opacity = '0.85';
            }, 500);
        }, 12000);

        // Плавное появление
        quoteEl.style.transition = 'opacity 0.5s';
    }

    /**
     * Часы
     */
    _initClock() {
        const clockEl = document.createElement('span');
        clockEl.style.marginLeft = 'auto';
        const statusBar = document.getElementById('status-bar');
        statusBar.appendChild(clockEl);

        const updateClock = () => {
            const now = new Date();
            clockEl.textContent = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
        };
        updateClock();
        setInterval(updateClock, 10000);
    }

    /**
     * Контекстное меню
     */
    _initContextMenu() {
        const menu = document.getElementById('context-menu');

        document.getElementById('desktop').addEventListener('contextmenu', (e) => {
            if (e.target.closest('.file-item')) return;
            e.preventDefault();
            menu.style.left = e.clientX + 'px';
            menu.style.top = e.clientY + 'px';
            menu.classList.remove('hidden');
        });

        document.addEventListener('click', () => menu.classList.add('hidden'));

        menu.querySelectorAll('.context-menu-item').forEach(item => {
            item.addEventListener('click', () => {
                const action = item.dataset.action;
                this._handleContextAction(action);
                menu.classList.add('hidden');
            });
        });

        // Клавиши
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Delete' && fileManagerApp.selectedItem) {
                fileManagerApp.deleteSelected();
            }
            if (e.key === 'F2' && fileManagerApp.selectedItem) {
                e.preventDefault();
                fileManagerApp.renameSelected();
            }
            if (e.key === 'Backspace' && !e.target.matches('input, textarea')) {
                fileManagerApp.navigateUp();
            }
        });
    }

    _handleContextAction(action) {
        switch (action) {
            case 'refresh':
                fileManagerApp.loadDirectory(fileManagerApp.currentPath);
                break;
            case 'mkdir':
                fileManagerApp.createFolder();
                break;
            case 'delete':
                fileManagerApp.deleteSelected();
                break;
            case 'rename':
                fileManagerApp.renameSelected();
                break;
        }
    }
}

window.desktop = new Desktop();
