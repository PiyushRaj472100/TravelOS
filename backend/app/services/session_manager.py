from typing import Any
from app.models.travel_state import TravelState


class SessionManager:

    def __init__(self):
        self.sessions: dict[str, TravelState] = {}
        # Per-session conversation history: list of {role, content}
        self.histories: dict[str, list[dict[str, str]]] = {}

    # =================================================
    # Travel State
    # =================================================

    def get_state(self, session_id: str) -> TravelState:
        if session_id not in self.sessions:
            self.sessions[session_id] = TravelState()
        return self.sessions[session_id]

    def save_state(
        self,
        session_id: str,
        state: TravelState
    ) -> None:
        self.sessions[session_id] = state

    # =================================================
    # Conversation History
    # =================================================

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        if session_id not in self.histories:
            self.histories[session_id] = []
        return self.histories[session_id]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """role: 'user' | 'assistant'"""
        if session_id not in self.histories:
            self.histories[session_id] = []

        self.histories[session_id].append({
            "role": role,
            "content": content
        })

        # Keep last 20 messages to avoid token bloat
        if len(self.histories[session_id]) > 20:
            self.histories[session_id] = (
                self.histories[session_id][-20:]
            )

    def get_history_text(self, session_id: str) -> str:
        """Format history as readable conversation text."""
        history = self.get_history(session_id)
        if not history:
            return ""
        lines = []
        for msg in history:
            role_label = (
                "User" if msg["role"] == "user" else "Assistant"
            )
            lines.append(f"{role_label}: {msg['content']}")
        return "\n".join(lines)

    # =================================================
    # Session Control
    # =================================================

    def delete_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.histories:
            del self.histories[session_id]


session_manager = SessionManager()