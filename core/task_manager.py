from __future__ import annotations

import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class TaskStatus:
    id: str
    state: str = "pending"
    progress: int = 0
    result: Any = None
    result_filename: str = ""
    result_mimetype: str = ""
    error: str | None = None
    created_at: float = field(default_factory=time.time)


class TaskManager:
    def __init__(self, max_workers: int = 2, ttl: int = 900):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: dict[str, TaskStatus] = {}
        self._lock = threading.Lock()
        self._ttl = ttl

    def submit(self, fn: Callable, *args, result_filename: str = "result", result_mimetype: str = "application/octet-stream", **kwargs) -> str:
        self._purge_expired()

        task_id = uuid.uuid4().hex
        task = TaskStatus(id=task_id, result_filename=result_filename, result_mimetype=result_mimetype)

        with self._lock:
            self._tasks[task_id] = task

        def _wrapped():
            with self._lock:
                task.state = "running"
            try:
                def _progress(current, total):
                    pct = int((current / total) * 100) if total > 0 else 0
                    with self._lock:
                        task.progress = pct

                result = fn(*args, progress_callback=_progress, **kwargs)

                with self._lock:
                    task.result = result
                    task.progress = 100
                    task.state = "complete"
            except Exception as exc:
                with self._lock:
                    task.error = str(exc)
                    task.state = "error"

        self._executor.submit(_wrapped)
        return task_id

    def get_status(self, task_id: str) -> dict | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return {
                "id": task.id,
                "state": task.state,
                "progress": task.progress,
                "error": task.error,
                "has_result": task.result is not None,
                "result_filename": task.result_filename,
                "result_mimetype": task.result_mimetype,
            }

    def get_result(self, task_id: str) -> tuple[Any, str, str] | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.state != "complete" or task.result is None:
                return None
            result = task.result
            filename = task.result_filename
            mimetype = task.result_mimetype
            # one download, then gone
            task.result = None
            return result, filename, mimetype

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.state == "pending":
                task.state = "error"
                task.error = "Cancelled by user."
                return True
            return False

    def _purge_expired(self):
        # RAM ain't infinite buddy
        now = time.time()
        with self._lock:
            expired = [tid for tid, t in self._tasks.items() if (now - t.created_at) > self._ttl]
            for tid in expired:
                task = self._tasks.pop(tid)
                if hasattr(task.result, "close"):
                    task.result.close()

    def shutdown(self):
        self._executor.shutdown(wait=False)
