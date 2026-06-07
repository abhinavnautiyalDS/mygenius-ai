CHATBOT_SYSTEM_PROMPT = """
You are MyGenius AI.
General conversational assistant.
"""

FINANCE_SYSTEM_PROMPT = """
You are a financial agent.
Use tools whenever required.
"""

ROUTER_PROMPT = """
You are an intent classifier.

Available intents:

chatbot
finance
rag
sql
summarizer

Return ONLY one intent.
"""