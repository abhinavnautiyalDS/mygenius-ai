from typing import TypedDict


class AgentState(
    TypedDict
):

    query: str

    file_path: str

    intent: str

    response: str

    session_id: str