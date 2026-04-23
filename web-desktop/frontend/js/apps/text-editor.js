/**
 * Приложение "Текстовый редактор"
 */

class TextEditorApp {
    constructor() {
        this.sessionId = null;
        this.currentPath = null;
        this.container = null;
        this.textarea = null;
    }

    /**
     * Открыть редактор (пустой)
     */
    open(sessionId) {
        this.sessionId = sessionId;
        this.currentPath = null;

        const win = windowManager.createWindow({
            title: 'Текстовый редактор',
            icon: '📝',
            width: 750,
            height: 550,
            content: `
                <div class="text-editor" id="te-${Date.now()}">
                    <div class="text-editor-toolbar">
                        <button class="btn-open">📂 Открыть</button>
                        <button class="btn-save">💾 Сохранить</button>
                        <button class="btn-save-as">💾 Сохранить как...</button>
                        <div class="text-editor-path">Новый файл</div>
                    </div>
                    <textarea placeholder="Начните вводить текст..."></textarea>
                </div>
            `
        });

        this.container = win.element.querySelector('.text-editor');
        this.textarea = this.container.querySelector('textarea');
        this._setupHandlers(win.id);

        return win;
    }

    /**
     * Открыть файл с сервера
     */
    async openFile(sessionId, path) {
        this.sessionId = sessionId;
        this.currentPath = path;

        const win = windowManager.createWindow({
            title: `Редактор: ${path.split('/').pop()}`,
            icon: '📝',
            width: 750,
            height: 550,
            content: `
                <div class="text-editor">
                    <div class="text-editor-toolbar">
                        <button class="btn-open">📂 Открыть</button>
                        <button class="btn-save">💾 Сохранить</button>
                        <button class="btn-save-as">💾 Сохранить как...</button>
                        <div class="text-editor-path">${path}</div>
                    </div>
                    <textarea placeholder="Загрузка..."></textarea>
                </div>
            `
        });

        this.container = win.element.querySelector('.text-editor');
        this.textarea = this.container.querySelector('textarea');
        this._setupHandlers(win.id);

        // Загружаем содержимое
        this.textarea.value = 'Загрузка...';
        this.textarea.disabled = true;

        try {
            const response = await fetch('/api/files/read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    path: path
                })
            });

            const data = await response.json();

            if (data.success) {
                this.textarea.value = data.content;
                this.textarea.disabled = false;
            } else {
                this.textarea.value = `Ошибка чтения файла: ${data.error}`;
                this.textarea.disabled = true;
            }
        } catch (err) {
            this.textarea.value = `Ошибка сети: ${err.message}`;
            this.textarea.disabled = true;
        }

        return win;
    }

    /**
     * Обработчики кнопок
     */
    _setupHandlers(windowId) {
        const toolbar = this.container.querySelector('.text-editor-toolbar');

        toolbar.querySelector('.btn-open').addEventListener('click', () => {
            this.openFilePrompt();
        });

        toolbar.querySelector('.btn-save').addEventListener('click', () => {
            this.saveFile();
        });

        toolbar.querySelector('.btn-save-as').addEventListener('click', () => {
            this.saveFileAs();
        });

        // Ctrl+S — сохранить
        this.textarea.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveFile();
            }
        });
    }

    /**
     * Сохранить файл
     */
    async saveFile() {
        if (!this.currentPath) {
            this.saveFileAs();
            return;
        }

        const content = this.textarea.value;

        try {
            const response = await fetch('/api/files/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    path: this.currentPath,
                    content: content
                })
            });

            const data = await response.json();

            if (data.success) {
                this._showStatus('✓ Сохранено', '#2e7d32');
            } else {
                this._showStatus('✗ Ошибка: ' + data.message, '#c62828');
            }
        } catch (err) {
            this._showStatus('✗ Ошибка сети: ' + err.message, '#c62828');
        }
    }

    /**
     * Сохранить как...
     */
    async saveFileAs() {
        const newPath = prompt('Путь для сохранения:', this.currentPath || '/home/');
        if (!newPath) return;

        this.currentPath = newPath;

        // Обновляем путь в UI
        const pathEl = this.container.querySelector('.text-editor-path');
        pathEl.textContent = newPath;

        // Обновляем заголовок окна
        const win = this.container.closest('.window');
        if (win) {
            const titleEl = win.querySelector('.window-title');
            titleEl.textContent = `Редактор: ${newPath.split('/').pop()}`;
        }

        await this.saveFile();
    }

    /**
     * Открыть файл (диалог)
     */
    async openFilePrompt() {
        const path = prompt('Путь к файлу:', '/');
        if (!path) return;

        if (window.fileManagerApp) {
            // Если файловый менеджер уже открыт, можно использовать его
            // Но пока просто откроем файл
        }

        this.openFile(this.sessionId, path);
    }

    /**
     * Показать статус
     */
    _showStatus(message, color) {
        const pathEl = this.container.querySelector('.text-editor-path');
        const originalText = pathEl.textContent;
        pathEl.textContent = message;
        pathEl.style.color = color;

        setTimeout(() => {
            pathEl.textContent = originalText;
            pathEl.style.color = '';
        }, 2000);
    }
}

window.textEditorApp = new TextEditorApp();
