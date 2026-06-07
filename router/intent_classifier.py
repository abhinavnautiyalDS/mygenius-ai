# ==================================================
# intent_classifier.py
# MyGenius AI Intent Classifier
# Built by Abhinav Nautiyal
# ==================================================


class IntentClassifier:

    def classify(
        self,
        query: str,
        file_uploaded: bool = False
    ) -> str:

        query = query.lower().strip()

        # =====================================
        # File Uploaded
        # =====================================

        if file_uploaded:

            summary_keywords = [

                "summary",
                "summarize",
                "summarise",
                "brief",
                "overview",
                "key points",
                "main points",
                "executive summary"
            ]

            if any(
                keyword in query
                for keyword in summary_keywords
            ):

                return "summarizer"

            return "rag"

        # =====================================
        # Finance Intent
        # =====================================

        finance_keywords = [

            "stock",
            "share",
            "price",
            "investment",
            "invest",
            "market",
            "trading",
            "finance",
            "financial",
            "loan",
            "emi",
            "mutual fund",
            "portfolio",
            "nifty",
            "sensex",
            "profit",
            "revenue"
        ]

        if any(
            keyword in query
            for keyword in finance_keywords
        ):

            return "finance"

        # =====================================
        # SQL Intent
        # =====================================

        sql_keywords = [

            "sql",
            "database",
            "table",
            "schema",
            "query",
            "select",
            "insert",
            "update",
            "delete",
            "join",
            "mysql",
            "postgresql",
            "sqlite"
        ]

        if any(
            keyword in query
            for keyword in sql_keywords
        ):

            return "sql"

        # =====================================
        # Default
        # =====================================

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

