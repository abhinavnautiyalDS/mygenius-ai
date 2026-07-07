# ==================================================
# summarizer_agent.py
# MyGenius AI - Document Summarizer
# Powered by Gemin
# Built by Abhinav Nautiyal
# ==================================================

import os
import sys
from pathlib import Path

from pypdf import PdfReader
from langchain_google_genai import (
    ChatGoogleGenerativeAI
)

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from config.settings import (
    GOOGLE_API_KEY
)


class SummarizerAgent:

    def __init__(self):

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3
        )

    # =====================================
    # Extract PDF Text
    # =====================================

    def extract_pdf_text(
        self,
        file_path: str
    ) -> str:

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:

            page_text = (
                page.extract_text()
            )

            if page_text:

                text += (
                    page_text + "\n\n"
                )

        return text.strip()

    # =====================================
    # Extract TXT Text
    # =====================================

    def extract_txt_text(
        self,
        file_path: str
    ) -> str:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            return f.read()

    # =====================================
    # Load Document
    # =====================================

    def load_document(
        self,
        file_path: str
    ) -> str:

        extension = (
            os.path.splitext(
                file_path
            )[1].lower()
        )

        if extension == ".pdf":

            return self.extract_pdf_text(
                file_path
            )

        elif extension == ".txt":

            return self.extract_txt_text(
                file_path
            )

        else:

            raise ValueError(
                "Unsupported file type."
            )

    # =====================================
    # Chunk Document
    # =====================================

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 6000
    ):

        chunks = []

        for i in range(
            0,
            len(text),
            chunk_size
        ):

            chunks.append(
                text[
                    i:i + chunk_size
                ]
            )

        return chunks

    # =====================================
    # Summarize Chunk
    # =====================================

    def summarize_chunk(
        self,
        chunk: str
    ) -> str:

        prompt = f"""
You are an expert document analyst.

Summarize the following document section.

Focus on:

- Key insights
- Important facts
- Risks
- Opportunities
- Actionable information

Document:

{chunk}
"""

        response = self.llm.invoke(
            prompt
        )

        return (
            response.content.strip()
        )

    # =====================================
    # Main Summarization
    # =====================================

    def invoke(
        self,
        file_path: str
    ):

        try:

            text = self.load_document(
                file_path
            )

            chunks = self.chunk_text(
                text
            )

            partial_summaries = []

            for chunk in chunks:

                summary = (
                    self.summarize_chunk(
                        chunk
                    )
                )

                partial_summaries.append(
                    summary
                )

            combined_summary = (
                "\n\n".join(
                    partial_summaries
                )
            )

            final_prompt = f"""
Create a final consolidated summary
from the following summaries.

Provide:

1. Executive Summary
2. Key Insights
3. Risks
4. Opportunities
5. Final Takeaways

Summaries:

{combined_summary}
"""

            final_response = (
                self.llm.invoke(
                    final_prompt
                )
            )

            final_summary = (
                final_response.content.strip()
            )

            return {

                "summary":
                final_summary,

                "chunks":
                len(chunks)
            }

        except Exception as e:

            return {

                "summary":
                f"Summarization Error: {e}",

                "chunks": 0
            }

    # =====================================
    # Clear Memory
    # =====================================

    def clear_memory(self):

        pass


# ==========================================
# Local Testing
# ==========================================

if __name__ == "__main__":

    agent = SummarizerAgent()

    result = agent.invoke(
        "data/documents/Sample-Financial-Statements-1.pdf"
    )

    print(
        "\nSummary:\n"
    )

    print(
        result["summary"]
    )

