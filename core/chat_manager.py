"""
ModelDock Studio - Persistent Chat & Project Manager
Safely preserves user chat conversations, multi-session history, and project workspaces
directly on disk so chats are 100% persistent across page refreshes, browser reloads,
and application restarts.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import threading

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHATS_FILE_PATH = DEFAULT_DATA_DIR / "chats.json"


class ChatManager:
    _instance = None
    _lock = threading.RLock()

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or CHATS_FILE_PATH
        self.data_dir = self.data_path.parent
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state: Dict[str, Any] = {
            "sessions": [],
            "projects": [
                {
                    "id": "proj_default",
                    "name": "Code & Analysis Workspace",
                    "description": "Project workspace for software engineering, deep reasoning, and document workflows.",
                    "icon": "📁",
                    "model": "",
                    "systemPrompt": "You are an expert technical AI assistant. Deliver concise, well-structured answers with clean code examples, type annotations, and architectural best practices.",
                    "createdAt": int(time.time() * 1000),
                }
            ],
        }
        self.load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load(self):
        with self._lock:
            if self.data_path.is_file():
                try:
                    content = self.data_path.read_text(encoding="utf-8")
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        if "sessions" in parsed and isinstance(parsed["sessions"], list):
                            self.state["sessions"] = parsed["sessions"]
                        if "projects" in parsed and isinstance(parsed["projects"], list) and len(parsed["projects"]) > 0:
                            self.state["projects"] = parsed["projects"]
                except Exception:
                    pass

    def save(self) -> bool:
        with self._lock:
            try:
                self.data_dir.mkdir(parents=True, exist_ok=True)
                temp_file = self.data_path.with_suffix(".tmp")
                temp_file.write_text(
                    json.dumps(self.state, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                temp_file.replace(self.data_path)
                return True
            except Exception:
                return False

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "sessions": list(self.state.get("sessions", [])),
                "projects": list(self.state.get("projects", [])),
            }

    def save_all(self, sessions: List[Dict[str, Any]], projects: List[Dict[str, Any]]) -> bool:
        with self._lock:
            self.state["sessions"] = sessions
            if projects:
                self.state["projects"] = projects
        return self.save()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for s in self.state.get("sessions", []):
                if s.get("id") == session_id:
                    return dict(s)
            return None

    def upsert_session(self, session: Dict[str, Any]) -> bool:
        with self._lock:
            sessions = self.state.get("sessions", [])
            sid = session.get("id")
            idx = next((i for i, s in enumerate(sessions) if s.get("id") == sid), -1)
            if idx >= 0:
                sessions[idx] = session
            else:
                sessions.insert(0, session)
            self.state["sessions"] = sessions
        return self.save()

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            self.state["sessions"] = [s for s in self.state.get("sessions", []) if s.get("id") != session_id]
        return self.save()

    def get_projects(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.state.get("projects", []))

    def upsert_project(self, project: Dict[str, Any]) -> bool:
        with self._lock:
            projects = self.state.get("projects", [])
            pid = project.get("id")
            idx = next((i for i, p in enumerate(projects) if p.get("id") == pid), -1)
            if idx >= 0:
                projects[idx] = project
            else:
                projects.append(project)
            self.state["projects"] = projects
        return self.save()

    def delete_project(self, project_id: str) -> bool:
        with self._lock:
            self.state["projects"] = [p for p in self.state.get("projects", []) if p.get("id") != project_id]
            # Unlink sessions from deleted project
            for s in self.state.get("sessions", []):
                if s.get("projectId") == project_id:
                    s["projectId"] = None
        return self.save()
