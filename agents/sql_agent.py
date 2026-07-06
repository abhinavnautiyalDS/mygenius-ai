# ==================================================
# sql_agent.py
# MyGenius AI - SQL Agent
# Built by Abhinav Nautiyal
# ==================================================

import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from langchain_google_genai import (
    ChatGoogleGenerativeAI
)

from config.settings import (
    GOOGLE_API_KEY
)


class SQLAgent:

    def __init__(
        self,
        db_path="data/sqlite/finance.db"
    ):

        self.db_path = db_path

        self.memory = {}

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )

    # =====================================
    # Database Schema
    # =====================================

    def get_schema(self):

        return """
Database: finance.db

Table: clients
Columns:
- client_id INTEGER
- client_name TEXT
- age INTEGER
- city TEXT
- risk_profile TEXT

Table: investments
Columns:
- investment_id INTEGER
- client_id INTEGER
- investment_type TEXT
- amount REAL
- investment_date TEXT

Relationship:
clients.client_id = investments.client_id
"""

    # =====================================
    # Generate SQL
    # =====================================

    def generate_sql(
        self,
        question: str
    ):

        prompt = f"""
You are an expert SQLite query generator.

Database Schema:

{self.get_schema()}

IMPORTANT RULES:

1. Return ONLY valid SQLite SQL.
2. Do NOT return markdown.
3. Do NOT use ```sql.
4. Do NOT explain anything.
5. Do NOT write 'SQL Query:'.
6. Do NOT write 'SQLite Query:'.
7. Do NOT write comments.
8. Generate a single SELECT query only.
9. Never use INSERT, UPDATE, DELETE,
   DROP, ALTER, CREATE.

Question:
{question}

SQL:
"""

        response = self.llm.invoke(
            prompt
        )

        sql = response.content.strip()

        # Clean Gemini output aggressively
        cleanup_strings = [
            "```sql",
            "```",
            "SQL Query:",
            "SQLite Query:",
            "Here is the SQL query:",
            "Here is your SQL query:",
            "SQL:",
        ]

        for item in cleanup_strings:
            sql = sql.replace(
                item,
                ""
            )

        sql = sql.strip()

        print("\nGenerated SQL:")
        print(sql)

        return sql

    # =====================================
    # Execute SQL
    # =====================================

    def execute_sql(
        self,
        sql_query: str
    ):

        conn = sqlite3.connect(
            self.db_path
        )

        cursor = conn.cursor()

        cursor.execute(
            sql_query
        )

        rows = cursor.fetchall()

        columns = []

        if cursor.description:

            columns = [
                desc[0]
                for desc in cursor.description
            ]

        conn.close()

        return {
            "columns": columns,
            "rows": rows
        }

    # =====================================
    # Generate Human Answer
    # =====================================

    def generate_answer(
        self,
        question: str,
        result: dict
    ):

        prompt = f"""
Question:
{question}

Database Result:
{result}

Provide a concise answer.

Do not mention SQL.
"""

        response = self.llm.invoke(
            prompt
        )

        return response.content.strip()

    # =====================================
    # Get Tables
    # =====================================

    def get_tables(self):

        try:

            conn = sqlite3.connect(
                self.db_path
            )

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table';
                """
            )

            tables = [
                row[0]
                for row in cursor.fetchall()
            ]

            conn.close()

            return tables

        except Exception as e:

            return [
                f"Error: {e}"
            ]

    # =====================================
    # Main Invoke
    # =====================================

    def invoke(
        self,
        query: str,
        session_id: str = "default"
    ):

        try:

            if session_id not in self.memory:

                self.memory[
                    session_id
                ] = []

            # Step 1
            sql_query = self.generate_sql(
                query
            )

            # Safety Check
            dangerous = [
                "INSERT",
                "UPDATE",
                "DELETE",
                "DROP",
                "ALTER",
                "CREATE"
            ]

            sql_upper = sql_query.upper()

            for keyword in dangerous:

                if keyword in sql_upper:

                    return (
                        "Unsafe SQL detected."
                    )

            # Step 2
            result = self.execute_sql(
                sql_query
            )

            # Step 3
            answer = self.generate_answer(
                query,
                result
            )

            self.memory[
                session_id
            ].append(
                {
                    "question": query,
                    "sql": sql_query,
                    "answer": answer
                }
            )

            return f"""
Answer:
{answer}

Generated SQL:
{sql_query}

Rows Returned:
{len(result['rows'])}
"""

        except Exception as e:

            return (
                f"SQL Agent Error: {e}"
            )

    # =====================================
    # Clear Memory
    # =====================================

    def clear_memory(
        self,
        session_id: str
    ):

        if session_id in self.memory:

            del self.memory[
                session_id
            ]


# ==========================================
# Local Testing
# ==========================================

if __name__ == "__main__":

    agent = SQLAgent()

    print(
        "\nAvailable Tables:"
    )

    print(
        agent.get_tables()
    )

    while True:

        query = input(
            "\nQuestion: "
        )

        if query.lower() == "exit":

            break

        answer = agent.invoke(
            query,
            session_id="test_user"
        )

        print(
            "\nResult:"
        )

        print(
            answer
        )
