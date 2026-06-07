
# ==================================================
# routing_logic.py
# MyGenius AI Router
# Built by Abhinav Nautiyal
# ==================================================

from agents.chatbot_agent import (
    ChatbotAgent
)

from agents.finance_agent import (
    FinanceAgent
)

from agents.rag_agent import (
    RAGAgent
)

from agents.sql_agent import (
    SQLAgent
)

from agents.summarizer_agent import (
    SummarizerAgent
)

from router.intent_classifier import (
    IntentClassifier
)


class Router:

    def __init__(self):

        # --------------------------------------
        # Intent Classifier
        # --------------------------------------
        self.classifier = (
            IntentClassifier()
        )

        # --------------------------------------
        # Agents
        # --------------------------------------
        self.chatbot = (
            ChatbotAgent()
        )

        self.finance = (
            FinanceAgent()
        )

        self.rag = (
            RAGAgent()
        )

        self.sql = (
            SQLAgent()
        )

        self.summarizer = (
            SummarizerAgent()
        )

    # =====================================
    # Main Routing Function
    # =====================================

    def route(
        self,
        query: str,
        file_path: str = None,
        session_id: str = "default"
    ):

        try:

            intent = (
                self.classifier.classify(
                    query=query,
                    has_file=file_path is not None
                )
            )

            print(
                f"[Router] Intent: {intent}"
            )

            # ----------------------------------
            # Chatbot Agent
            # ----------------------------------

            if intent == "chatbot":

                return (
                    self.chatbot.invoke(
                        query,
                        session_id
                    )
                )

            # ----------------------------------
            # Finance Agent
            # ----------------------------------

            elif intent == "finance":

                return (
                    self.finance.invoke(
                        query,
                        session_id
                    )
                )

            # ----------------------------------
            # SQL Agent
            # ----------------------------------

            elif intent == "sql":

                return (
                    self.sql.invoke(
                        query
                    )
                )

            # ----------------------------------
            # Summarizer Agent
            # ----------------------------------

            elif intent == "summarizer":

                if not file_path:

                    return (
                        "No document provided."
                    )

                return (
                    self.summarizer.invoke(
                        file_path
                    )
                )

            # ----------------------------------
            # RAG Agent
            # ----------------------------------

            elif intent == "rag":

                if not file_path:

                    return {
                        "answer":
                        "No document loaded.",

                        "sources": []
                    }

                # Build RAG Index
                self.rag.load_document(
                    file_path,
                    session_id
                )

                return (
                    self.rag.invoke(
                        query,
                        session_id
                    )
                )

            # ----------------------------------
            # Fallback
            # ----------------------------------

            return (
                self.chatbot.invoke(
                    query,
                    session_id
                )
            )

        except Exception as e:

            return (
                f"Router Error: {e}"
            )

    # =====================================
    # Clear Session
    # =====================================

    def clear_session(
        self,
        session_id: str
    ):

        try:

            self.chatbot.clear_memory(
                session_id
            )

        except:
            pass

        try:

            self.finance.clear_memory(
                session_id
            )

        except:
            pass

        try:

            self.rag.clear_session(
                session_id
            )

        except:
            pass


# ==========================================
# Local Testing
# ==========================================

if __name__ == "__main__":

    router = Router()

    while True:

        query = input(
            "\nUser: "
        )

        if query.lower() == "exit":
            break

        response = router.route(
            query=query,
            session_id="test_user"
        )

        print(
            "\nAssistant:\n"
        )

        print(response)

