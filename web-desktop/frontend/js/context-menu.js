/**
 * Контекстное меню рабочего стола
 */

class ContextMenu {
    constructor() {
        this.menu = document.getElementById('context-menu');
    }

    show(x, y) {
        if (!this.menu) return;
        this.menu.style.left = x + 'px';
        this.menu.style.top = y + 'px';
        this.menu.classList.remove('hidden');
    }

    close() {
        if (!this.menu) return;
        this.menu.classList.add('hidden');
    }
}

window.contextMenu = new ContextMenu();
