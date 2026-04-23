/**
 * Файловый менеджер — теперь на весь экран
 */

class FileManagerApp {
    constructor() {
        this.sessionId = null;
        this.currentPath = '/';
        this.selectedItem = null;
        this.entries = [];
        this.navStack = [];

        // DOM элементы
        this.fileListEl = null;
        this.pathEl = null;
        this.btnBack = null;
        this.statusText = null;
    }

    /**
     * Инициализация после подключения
     */
    init(sessionId) {
        this.sessionId = sessionId;
        this.currentPath = '/';
        this.navStack = [];
        this.selectedItem = null;

        this.fileListEl = document.getElementById('file-list');
        this.pathEl = document.getElementById('current-path');
        this.btnBack = document.getElementById('btn-back');
        this.statusText = document.getElementById('status-text');

        this._bindEvents();
        this.loadDirectory('/');
    }

    /**
     * Привязка событий
     */
    _bindEvents() {
        document.getElementById('btn-back').addEventListener('click', () => this.navigateUp());
        document.getElementById('btn-refresh').addEventListener('click', () => this.loadDirectory(this.currentPath));
        document.getElementById('btn-mkdir').addEventListener('click', () => this.createFolder());

        // Клик на пустом месте — снять выделение
        this.fileListEl.addEventListener('click', (e) => {
            if (e.target === this.fileListEl) {
                this._deselectAll();
                this.selectedItem = null;
            }
        });
    }

    /**
     * Загрузить директорию
     */
    async loadDirectory(path) {
        this.currentPath = path;
        this.pathEl.textContent = path;
        this.selectedItem = null;
        this.entries = [];

        this.fileListEl.innerHTML = '<div class="loading">Загрузка...</div>';
        this.statusText.textContent = 'Загрузка...';

        try {
            const response = await fetch('/api/files/list', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId, path })
            });

            const data = await response.json();

            if (data.success) {
                this.entries = data.entries;
                this._renderFiles();
                this.statusText.textContent = `Элементов: ${data.entries.length}`;
            } else {
                this.fileListEl.innerHTML = `<div style="padding:30px;text-align:center;color:#c62828;">Ошибка: ${data.error}</div>`;
                this.statusText.textContent = 'Ошибка';
            }
        } catch (err) {
            this.fileListEl.innerHTML = `<div style="padding:30px;text-align:center;color:#c62828;">Ошибка сети: ${err.message}</div>`;
            this.statusText.textContent = 'Ошибка сети';
        }

        // Кнопка назад
        this.btnBack.disabled = path === '/';
    }

    /**
     * Отрисовка файлов
     */
    _renderFiles() {
        this.fileListEl.innerHTML = '';

        if (this.entries.length === 0) {
            this.fileListEl.innerHTML = '<div class="empty-dir">📂 Папка пуста</div>';
            return;
        }

        this.entries.forEach((entry, index) => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.dataset.index = index;

            const icon = entry.is_dir ? '📁' : this._getFileIcon(entry.name);
            const size = entry.is_dir ? '' : this._formatSize(entry.size);
            const modified = entry.modified ? this._formatDate(entry.modified) : '';

            item.innerHTML = `
                <span class="file-icon">${icon}</span>
                <span class="file-name">${entry.name}</span>
                <span class="file-modified">${modified}</span>
                <span class="file-size">${size}</span>
            `;

            // Клик — выбрать
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                this._selectItem(index, item);
            });

            // Двойной клик — открыть
            item.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                this._openItem(index);
            });

            this.fileListEl.appendChild(item);
        });
    }

    /**
     * Выделить элемент
     */
    _selectItem(index, element) {
        this._deselectAll();
        element.classList.add('selected');
        this.selectedItem = { index, entry: this.entries[index] };
    }

    /**
     * Снять выделение
     */
    _deselectAll() {
        this.fileListEl.querySelectorAll('.file-item').forEach(el => el.classList.remove('selected'));
    }

    /**
     * Открыть файл/папку
     */
    _openItem(index) {
        const entry = this.entries[index];
        if (!entry) return;

        if (entry.is_dir) {
            this._openDirectory(entry.name);
        } else {
            // Файл — скачать и открыть
            this._openFile(entry.name);
        }
    }

    /**
     * Скачать и открыть файл
     */
    async _openFile(filename) {
        const fullPath = this.currentPath === '/' ? '/' + filename : this.currentPath + '/' + filename;

        this.statusText.textContent = `Скачивание: ${filename}...`;

        // Скачиваем через ссылку с download атрибутом
        const dlUrl = `/api/files/download-direct?path=${encodeURIComponent(fullPath)}&session=${this.sessionId}`;

        // Создаём невидимую ссылку и кликаем
        const a = document.createElement('a');
        a.href = dlUrl;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        this.statusText.textContent = `Скачан: ${filename}`;
    }

    /**
     * Открыть папку
     */
    _openDirectory(dirName) {
        this.navStack.push(this.currentPath);
        const newPath = this.currentPath === '/' ? '/' + dirName : this.currentPath + '/' + dirName;
        this.loadDirectory(newPath);
    }

    /**
     * Назад
     */
    navigateUp() {
        if (this.currentPath === '/') return;

        if (this.navStack.length > 0) {
            const parentPath = this.navStack.pop();
            this.loadDirectory(parentPath);
        } else {
            // Вычисляем родительскую директорию
            const parts = this.currentPath.split('/').filter(Boolean);
            parts.pop();
            const parentPath = '/' + parts.join('/') || '/';
            this.loadDirectory(parentPath);
        }
    }

    /**
     * Создать папку
     */
    async createFolder() {
        const name = prompt('Имя новой папки:');
        if (!name || !name.trim()) return;

        const path = this.currentPath === '/' ? '/' + name : this.currentPath + '/' + name;

        try {
            const response = await fetch('/api/files/mkdir', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId, path })
            });

            const data = await response.json();
            if (data.success) {
                this.loadDirectory(this.currentPath);
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (err) {
            alert('Ошибка сети: ' + err.message);
        }
    }

    /**
     * Удалить выбранный элемент
     */
    async deleteSelected() {
        if (!this.selectedItem) return;

        const entry = this.selectedItem.entry;
        if (!confirm(`Удалить "${entry.name}"?`)) return;

        const path = this.currentPath === '/' ? '/' + entry.name : this.currentPath + '/' + entry.name;

        try {
            const response = await fetch('/api/files/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId, path })
            });

            const data = await response.json();
            if (data.success) {
                this.loadDirectory(this.currentPath);
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (err) {
            alert('Ошибка сети: ' + err.message);
        }
    }

    /**
     * Переименовать выбранный элемент
     */
    async renameSelected() {
        if (!this.selectedItem) return;

        const entry = this.selectedItem.entry;
        const newName = prompt('Новое имя:', entry.name);
        if (!newName || newName === entry.name) return;

        const oldPath = this.currentPath === '/' ? '/' + entry.name : this.currentPath + '/' + entry.name;
        const newPath = this.currentPath === '/' ? '/' + newName : this.currentPath + '/' + newName;

        try {
            const response = await fetch('/api/files/rename', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId, path: oldPath, new_path: newPath })
            });

            const data = await response.json();
            if (data.success) {
                this.loadDirectory(this.currentPath);
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch (err) {
            alert('Ошибка сети: ' + err.message);
        }
    }

    /**
     * Иконка файла
     */
    _getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            'txt': '📄', 'md': '📄', 'py': '🐍', 'js': '📜',
            'html': '🌐', 'css': '🎨', 'json': '📋', 'yaml': '⚙️',
            'yml': '⚙️', 'log': '📃', 'sh': '⚡', 'bat': '⚡',
            'jpg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'svg': '🖼️',
            'zip': '📦', 'tar': '📦', 'gz': '📦', 'mp3': '🎵',
            'mp4': '🎬', 'pdf': '📕'
        };
        return icons[ext] || '📄';
    }

    /**
     * Форматировать размер
     */
    _formatSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    /**
     * Форматировать дату
     */
    _formatDate(timestamp) {
        if (!timestamp) return '';
        const d = new Date(timestamp * 1000);
        const day = String(d.getDate()).padStart(2, '0');
        const mon = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        const h = String(d.getHours()).padStart(2, '0');
        const m = String(d.getMinutes()).padStart(2, '0');
        return `${day}.${mon}.${year} ${h}:${m}`;
    }
}

window.fileManagerApp = new FileManagerApp();
