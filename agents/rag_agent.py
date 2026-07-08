# ==================================================
# rag_agent.p
# MyGenius AI - RAG Agent
# Gemini + FAISS Version
# Built by Abhinav Nautiyal
# =================================================

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from langchain_community.document_loaders import PyPDFLoader

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from langchain_community.vectorstores import (
    FAISS
)

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)

from config.settings import (
    GOOGLE_API_KEY
)


class RAGAgent:

    def __init__(self):

        # --------------------------------------
        # Session Stores
        # --------------------------------------
        self.vectorstores = {}
        self.retrievers = {}
        self.chat_history = {}

        # --------------------------------------
        # Gemini Embeddings
        # --------------------------------------
        self.embeddings = (
            GoogleGenerativeAIEmbeddings(
                model="gemini-embedding-001",
                google_api_key=GOOGLE_API_KEY
            )
        )

        # --------------------------------------
        # Gemini LLM
        # --------------------------------------
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.2
        )

    # =====================================
    # Build RAG Pipeline
    # =====================================

    def build_pipeline(
        self,
        file_path: str,
        session_id: str
    ):

        try:

            loader = PyPDFLoader(file_path)

            documents = loader.load()

            splitter = (
                RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
            )

            chunks = splitter.split_documents(
                documents
            )

            vectorstore = (
                FAISS.from_documents(
                    chunks,
                    self.embeddings
                )
            )

            retriever = (
                vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={
                        "k": 5
                    }
                )
            )

            self.vectorstores[
                session_id
            ] = vectorstore

            self.retrievers[
                session_id
            ] = retriever

            self.chat_history[
                session_id
            ] = []

        except Exception as e:

            raise Exception(
                f"Failed to build RAG pipeline: {e}"
            )

    # =====================================
    # Load Document
    # =====================================

    def load_document(
        self,
        file_path: str,
        session_id: str
    ):

        self.build_pipeline(
            file_path,
            session_id
        )

    # =====================================
    # Ask Question
    # =====================================

    def invoke(
        self,
        query: str,
        session_id: str
    ):

        if session_id not in self.retrievers:

            return {
                "answer":
                "No document loaded.",
                "sources": []
            }

        try:

            docs = (
                self.retrievers[
                    session_id
                ].invoke(query)
            )

            context = "\n\n".join(
                [
                    doc.page_content
                    for doc in docs
                ]
            )

            prompt = f"""
You are MyGenius AI RAG Agent.

Answer ONLY using the context provided.

Rules:
1. If answer exists in context, answer clearly.
2. If answer is not available, say:
   "The answer is not found in the document."
3. Do not hallucinate.
4. Be concise.

Context:
{context}

Question:
{query}
"""

            response = self.llm.invoke(
                prompt
            )

            answer = response.content

            sources = []

            for doc in docs:

                sources.append(
                    {
                        "page":
                        doc.metadata.get(
                            "page",
                            "?"
                        ),

                        "preview":
                        doc.page_content[
                            :200
                        ]
                    }
                )

            self.chat_history[
                session_id
            ].append(
                {
                    "question":
                    query,

                    "answer":
                    answer
                }
            )

            return {
                "answer":
                answer,

                "sources":
                sources
            }

        except Exception as e:

            return {
                "answer":
                f"RAG Error: {e}",

                "sources":
                []
            }

    # =====================================
    # Clear Session
    # =====================================

    def clear_session(
        self,
        session_id: str
    ):

        self.vectorstores.pop(
            session_id,
            None
        )

        self.retrievers.pop(
            session_id,
            None
        )

        self.chat_history.pop(
            session_id,
            None
        )


# ==========================================
# Local Testing
# ==========================================

if __name__ == "__main__":

    agent = RAGAgent()

    pdf_path = (
        "data/documents/Sample-Financial-Statements-1.pdf"
    )

    agent.load_document(
        pdf_path,
        "test_user"
    )

    while True:

        question = input(
            "\nQuestion: "
        )

        if question.lower() == "exit":
            break

        result = agent.invoke(
            question,
            "test_user"
        )

        print(
            "\nAnswer:\n",
            result["answer"]
        )

        print(
            "\nSources Found:",
            len(result["sources"])
        )

        for source in result["sources"]:

            print(
                f"\nPage: {source['page']}"
            )
