"""
FastAPI сервер для веб-десктопа
WebSocket терминал + REST API для файлов
"""

import json
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from ssh_manager import SSHSession
from file_manager import FileManager


# Хранилище сессий
sessions: dict[str, SSHSession] = {}
active_websockets: dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запуск и остановка сервера"""
    print("SSH Desktop server started!")
    yield
    # Очистка при остановке
    for sid, session in sessions.items():
        session.close()
    sessions.clear()


app = FastAPI(title="SSH Web Desktop", lifespan=lifespan)


# === Модели данных ===

class ConnectRequest(BaseModel):
    hostname: str
    port: int = 22
    username: str
    password: Optional[str] = None
    key_file: Optional[str] = None


class FileListRequest(BaseModel):
    session_id: str
    path: str = "/"


class FileReadRequest(BaseModel):
    session_id: str
    path: str


class FileSaveRequest(BaseModel):
    session_id: str
    path: str
    content: str


class FileActionRequest(BaseModel):
    session_id: str
    path: str
    new_path: Optional[str] = None


class TerminalInput(BaseModel):
    session_id: str
    data: str


class TerminalResize(BaseModel):
    session_id: str
    cols: int
    rows: int


# === Статика (фронтенд) ===

import os as _os
import sys as _sys

# В PyInstaller данные лежат в _MEIPASS
def _resource_path(relative_path):
    """Получить абсолютный путь к ресурсу (работает и в .exe, и локально)"""
    try:
        base_path = _sys._MEIPASS
    except Exception:
        base_path = _os.path.abspath(".")

    # Пробуем разные варианты
    paths_to_try = [
        _os.path.join(base_path, relative_path),
        _os.path.join(base_path, "..", relative_path),
        _os.path.join(_os.path.dirname(__file__), "..", relative_path),
    ]

    for path in paths_to_try:
        if _os.path.isdir(path) or _os.path.isfile(path):
            return _os.path.abspath(path)

    # По умолчанию
    return _os.path.join(base_path, relative_path)

_frontend_dir = _resource_path("frontend")
print(f"Frontend: {_frontend_dir}")
print(f"Exists: {_os.path.isdir(_frontend_dir)}")

if _os.path.isdir(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")


@app.get("/")
async def index():
    """Главная страница — рабочий стол"""
    html_path = _resource_path("frontend/index.html")
    return FileResponse(html_path)


# === SSH Подключение ===

@app.post("/api/connect")
async def connect(req: ConnectRequest):
    """Создать SSH подключение"""
    session_id = str(uuid.uuid4())[:8]
    session = SSHSession(session_id)

    success, message = session.connect(
        hostname=req.hostname,
        port=req.port,
        username=req.username,
        password=req.password,
        key_file=req.key_file
    )

    if success:
        sessions[session_id] = session
        return {"success": True, "session_id": session_id, "message": message}
    else:
        return {"success": False, "session_id": None, "message": message}


@app.post("/api/disconnect")
async def disconnect(session_id: str):
    """Закрыть SSH подключение"""
    if session_id in sessions:
        sessions[session_id].close()
        del sessions[session_id]
        return {"success": True, "message": "Отключено"}
    return {"success": False, "message": "Сессия не найдена"}


# === Файловый менеджер ===

@app.post("/api/files/list")
async def file_list(req: FileListRequest):
    """Список файлов"""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session = sessions[req.session_id]
    fm = FileManager(session)
    success, entries, error = fm.list_directory(req.path)

    if success:
        return {"success": True, "entries": entries, "path": req.path}
    else:
        return {"success": False, "error": error}


@app.post("/api/files/read")
async def file_read(req: FileReadRequest):
    """Чтение файла"""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session = sessions[req.session_id]
    fm = FileManager(session)
    success, content, error = fm.read_file(req.path)

    if success:
        return {"success": True, "content": content}
    else:
        return {"success": False, "error": error}


@app.post("/api/files/save")
async def file_save(req: FileSaveRequest):
    """Сохранение файла"""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session = sessions[req.session_id]
    fm = FileManager(session)
    success, message = fm.save_file(req.path, req.content)

    return {"success": success, "message": message}


@app.post("/api/files/delete")
async def file_delete(req: FileActionRequest):
    """Удаление файла/папки"""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session = sessions[req.session_id]
    fm = FileManager(session)
    success, message = fm.delete(req.path)

    return {"success": success, "message": message}


@app.post("/api/files/rename")
async def file_rename(req: FileActionRequest):
    """Переименование"""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if not req.new_path:
        raise HTTPException(status_code=400, detail="Нужен new_path")

    session = sessions[req.session_id]
    fm = FileManager(session)
    success, message = fm.rename(req.path, req.new_path)

    return {"success": success, "message": message}


@app.post("/api/files/download")
async def file_download(req: FileReadRequest):
    """Скачать файл (для открытия)"""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session = sessions[req.session_id]
    fm = FileManager(session)

    import tempfile
    import os as _os2

    success, content, error = fm.read_file(req.path)
    if not success:
        return {"success": False, "error": error}

    # Сохраняем во временный файл для отдачи
    temp_dir = tempfile.gettempdir()
    temp_path = _os2.path.join(temp_dir, _os2.path.basename(req.path))
    with open(temp_path, 'wb') as f:
        f.write(content.encode('utf-8') if isinstance(content, str) else content)

    return {"success": True, "local_path": temp_path}


from fastapi.responses import FileResponse as FastAPIFileResponse, StreamingResponse


@app.get("/api/files/download-direct")
async def download_file_direct(path: str, session: str):
    """Скачать файл напрямую (браузер предложит сохранить)"""
    if session not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    import urllib.parse
    remote_path = urllib.parse.unquote(path)

    fm = FileManager(sessions[session])
    success, content, error = fm.read_file(remote_path)
    if not success:
        raise HTTPException(status_code=404, detail=error)

    # Определяем MIME-тип по расширению
    import mimetypes
    filename = remote_path.split('/')[-1]
    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        content_type = 'application/octet-stream'

    from io import BytesIO
    data = BytesIO(content.encode('utf-8') if isinstance(content, str) else content)

    return StreamingResponse(
        data,
        media_type=content_type,
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


@app.post("/api/files/mkdir")
async def file_mkdir(req: FileActionRequest):
    """Создание папки"""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    session = sessions[req.session_id]
    fm = FileManager(session)
    success, message = fm.mkdir(req.path)

    return {"success": success, "message": message}


# === WebSocket терминал ===

@app.websocket("/ws/terminal/{session_id}")
async def terminal_websocket(ws: WebSocket, session_id: str):
    """WebSocket для интерактивного терминала"""
    if session_id not in sessions:
        await ws.close(code=4004, reason="Сессия не найдена")
        return

    await ws.accept()
    active_websockets[session_id] = ws
    session = sessions[session_id]

    # Callback для получения вывода
    def on_output(data: str):
        try:
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                ws.send_text(json.dumps({"type": "output", "data": data}))
            )
        except Exception:
            pass

    session.add_callback(on_output)

    try:
        while True:
            message = await ws.receive_text()
            data = json.loads(message)

            if data.get("type") == "input":
                session.send_input(data["data"])
            elif data.get("type") == "resize":
                session.resize(data["cols"], data["rows"])

    except WebSocketDisconnect:
        pass
    finally:
        session.remove_callback(on_output)
        if session_id in active_websockets:
            del active_websockets[session_id]


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
