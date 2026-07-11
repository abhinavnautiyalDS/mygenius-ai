# ==================================================
# chatbot_agent.py
# MyGenius AI - Conversational Agent
# Powered by Gemini
# Built by Abhinav Nautiya
# =================================================
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder
)

from langchain_core.chat_history import (
    InMemoryChatMessageHistory
)

from langchain_core.runnables.history import (
    RunnableWithMessageHistory
)

from config.settings import GOOGLE_API_KEY


class ChatbotAgent:

    def __init__(self):

        # ------------------------------------------
        # Session Memory Store
        # ------------------------------------------
        self.store = {}

        # ------------------------------------------
        # Gemini LLM
        # ------------------------------------------
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7,
        )

        # ------------------------------------------
        # Prompt
        # ------------------------------------------
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are MyGenius AI.

                    You are the default conversational assistant.

                    Responsibilities:
                    - Answer general questions
                    - Explain concepts
                    - Help users learn
                    - Assist with problem solving
                    - Provide clear and concise responses

                    If a task requires:
                    - Financial analysis
                    - Document retrieval
                    - Summarization
                    - Database querying
                    - Tool execution

                    Those tasks are handled by specialized
                    agents inside MyGenius AI.

                    Be helpful, accurate, and professional.
                    """
                ),

                MessagesPlaceholder(
                    variable_name="history"
                ),

                (
                    "human",
                    "{input}"
                )
            ]
        )

        self.chain = self.prompt | self.llm

        # ------------------------------------------
        # Memory-enabled Conversation
        # ------------------------------------------
        self.conversation = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )

    # ------------------------------------------
    # Session History
    # ------------------------------------------
    def get_session_history(
        self,
        session_id: str
    ):

        if session_id not in self.store:

            self.store[session_id] = (
                InMemoryChatMessageHistory()
            )

        return self.store[session_id]

    # ------------------------------------------
    # Invoke Agent
    # ------------------------------------------
    def invoke(
        self,
        query: str,
        session_id: str = "default"
    ) -> str:

        try:

            response = self.conversation.invoke(
                {
                    "input": query
                },
                config={
                    "configurable": {
                        "session_id": session_id
                    }
                }
            )

            return response.content.strip()

        except Exception as e:

            error_str = str(e).lower()

            if "quota" in error_str or "429" in error_str:

                return (
                    "⚠️ Gemini API quota exceeded. "
                    "Please try again later."
                )

            elif (
                "api key" in error_str
                or "authentication" in error_str
                or "permission" in error_str
            ):

                return (
                    f"⚠️ Authentication issue: {str(e)}"
                )

            else:

                return (
                    f"⚠️ Error: {str(e)}"
                )

    # ------------------------------------------
    # Clear Memory
    # ------------------------------------------
    def clear_memory(
        self,
        session_id: str
    ):

        if session_id in self.store:
            del self.store[session_id]


# --------------------------------------------------
# Local Testing
# --------------------------------------------------
if __name__ == "__main__":

    agent = ChatbotAgent()

    while True:

        query = input("\nUser: ")

        if query.lower() == "exit":
            break

        response = agent.invoke(
            query,
            session_id="test_user"
        )

        print("\nAssistant:", response)
