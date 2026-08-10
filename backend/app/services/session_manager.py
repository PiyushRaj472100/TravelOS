from app.models.travel_state import TravelState


class SessionManager:

    def __init__(self):
        self.sessions: dict[str, TravelState] = {}

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

    def delete_session(self, session_id: str) -> None:

        if session_id in self.sessions:
            del self.sessions[session_id]
            
session_manager = SessionManager()            