/**
 * Приложение "Терминал" — xterm.js + WebSocket
 */

class TerminalApp {
    constructor() {
        this.term = null;
        this.fitAddon = null;
        this.ws = null;
        this.sessionId = null;
        this.container = null;
    }

    /**
     * Открыть терминал в новом окне
     */
    open(sessionId) {
        this.sessionId = sessionId;

        // Создаём окно
        const win = windowManager.createWindow({
            title: 'Терминал',
            icon: '⌨️',
            width: 800,
            height: 550,
            content: '<div class="terminal-container" id="term-container-' + Date.now() + '"></div>'
        });

        this.container = win.element.querySelector('.terminal-container');
        this.container.id = 'terminal-' + win.id;

        // Инициализируем xterm
        this._initTerminal(win.id);

        // Подключаем WebSocket
        this._connectWebSocket(win.id);

        // При resize окна
        setTimeout(() => this._fitTerminal(), 100);

        return win;
    }

    /**
     * Инициализация xterm.js
     */
    _initTerminal(windowId) {
        this.term = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Consolas, "Courier New", monospace',
            theme: {
                background: '#1e1e1e',
                foreground: '#d4d4d4',
                cursor: '#d4d4d4',
                selectionBackground: '#3a3a3a',
                black: '#1e1e1e',
                red: '#f48771',
                green: '#6a9955',
                yellow: '#dcdcaa',
                blue: '#569cd6',
                magenta: '#c586c0',
                cyan: '#4dc9b0',
                white: '#d4d4d4',
                brightBlack: '#808080',
                brightRed: '#f48771',
                brightGreen: '#6a9955',
                brightYellow: '#dcdcaa',
                brightBlue: '#569cd6',
                brightMagenta: '#c586c0',
                brightCyan: '#4dc9b0',
                brightWhite: '#ffffff'
            },
            allowProposedApi: true
        });

        this.fitAddon = new FitAddon.FitAddon();
        this.term.loadAddon(this.fitAddon);

        // Открываем в контейнере
        this.term.open(this.container);
        this.term.writeln('\x1b[32m🐶 SSH Web Terminal подключён\x1b[0m');
        this.term.writeln('\x1b[90mВведите команду...\x1b[0m');
        this.term.write('\r\n');

        // Обработка ввода
        this.term.onData((data) => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'input', data: data }));
            }
        });

        // При resize
        this.term.onResize((size) => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'resize', cols: size.cols, rows: size.rows }));
            }
        });

        this._fitTerminal();
    }

    /**
     * Подогнать размер терминала под контейнер
     */
    _fitTerminal() {
        if (this.fitAddon) {
            this.fitAddon.fit();
        }
    }

    /**
     * Подключение WebSocket
     */
    _connectWebSocket(windowId) {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${location.host}/ws/terminal/${this.sessionId}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.term.writeln('\x1b[32m✓ WebSocket подключён\x1b[0m');

            // Отправляем начальный размер
            if (this.term) {
                this.ws.send(JSON.stringify({
                    type: 'resize',
                    cols: this.term.cols,
                    rows: this.term.rows
                }));
            }
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'output' && this.term) {
                this.term.write(data.data);
            }
        };

        this.ws.onerror = () => {
            this.term.writeln('\x1b[31m✗ Ошибка WebSocket\x1b[0m');
        };

        this.ws.onclose = () => {
            this.term.writeln('\x1b[31m✗ Соединение закрыто\x1b[0m');
        };
    }

    /**
     * Обновить размер при resize окна
     */
    onResize() {
        this._fitTerminal();
    }
}

window.terminalApp = new TerminalApp();
