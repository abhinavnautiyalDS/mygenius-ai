# ==================================================
# intent_classifier.py
# MyGenius AI Intent Classifier
# Built by Abhinav Nautiyal
# ==================================================


class IntentClassifier:
    

    # def classify(
#         self,
#         query: str,
#         file_uploaded: bool = False
#     ) -> str:

#         query = query.lower().strip()

#         # =====================================
#         # File Uploaded
#         # =====================================

#         if file_uploaded:

#             summary_keywords = [

#                 "summary",
#                 "summarize",
#                 "summarise",
#                 "brief",
#                 "overview",
#                 "key points",
#                 "main points",
#                 "executive summary"
#             ]

#             if any(
#                 keyword in query
#                 for keyword in summary_keywords
#             ):

#                 return "summarizer"

#             return "rag"

#         # =====================================
#         # Finance Intent
#         # =====================================

#         finance_keywords = [

#             "stock",
#             "share",
#             "price",
#             "investment",
#             "invest",
#             "market",
#             "trading",
#             "finance",
#             "financial",
#             "loan",
#             "emi",
#             "mutual fund",
#             "portfolio",
#             "nifty",
#             "sensex",
#             "profit",
#             "revenue"
#         ]

#         if any(
#             keyword in query
#             for keyword in finance_keywords
#         ):

#             return "finance"

#         # =====================================
#         # SQL Intent
#         # =====================================

#         sql_keywords = [

#             "sql",
#             "database",
#             "table",
#             "schema",
#             "query",
#             "select",
#             "insert",
#             "update",
#             "delete",
#             "join",
#             "mysql",
#             "postgresql",
#             "sqlite",
#             "customer",
#             "customers",
#             "client",
#             "clients",
#             "investor",
#             "investors",
#             "records",
#             "show all",
#             "list all",
#             "top investors",
#             "highest investment"

#         ]

#         if any(
#             keyword in query
#             for keyword in sql_keywords
#         ):

#             return "sql"

#         # =====================================
#         # Default
#         # =====================================

#         return "chatbot"
    def classify(
            self,
            query: str,
            file_uploaded: bool = False
        ) -> str:
            query = query.lower().strip()

            # 1. If a file is uploaded, check for Summarization first
            if file_uploaded:
                summary_keywords = ["summary", "summarize", "summarise", "brief", "overview", "key points"]
                if any(k in query for k in summary_keywords):
                    return "summarizer"

            # 2. Check for SQL/Finance (Specific tools)
            sql_keywords = ["sql", "database", "table", "show all customers", "list investors"]
            if any(k in query for k in sql_keywords):
                return "sql"

            finance_keywords = ["stock", "price", "emi", "investment", "portfolio", "nifty"]
            if any(k in query for k in finance_keywords):
                return "finance"

            # 3. CRITICAL FIX: If a file is uploaded and it's not SQL/Finance, 
            # it MUST be a question about the document (RAG).
            if file_uploaded:
                return "rag"

            # 4. Default to Chatbot only if no file is present
            return "chatbot"


# ==========================================
# Local Testing
# ==========================================



if __name__ == "__main__":

    classifier = IntentClassifier()

    while True:

        query = input("\nQuery: ")

        if query.lower() == "exit":
            break

        intent = classifier.classify(
            query=query,
            file_uploaded=False
        )

        print(
            f"\nIntent: {intent}"
        )

