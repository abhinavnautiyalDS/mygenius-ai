# ==================================================
# finance_agent.py=
# MyGenius AI - Financial Agent
# Gemini Version
# Built by Abhinav Nautiyal
# =================================================

import sys
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

from config.settings import (
    GOOGLE_API_KEY,
    ALPHA_VANTAGE_API_KEY
)


# ==================================================
# TOOLS
# ==================================================

@tool
def calculator(expression: str) -> str:
    """
    Calculate EMI or simple math.
    Example:
    EMI(2000000, 0.09, 60)
    """

    try:

        if expression.startswith("EMI("):

            args = expression[4:-1].split(",")

            P = float(args[0].strip())
            r_annual = float(args[1].strip())
            n = int(args[2].strip())

            r_monthly = r_annual / 12

            if r_monthly == 0:
                return f"EMI: ₹{P/n:.2f}"

            emi = (
                P
                * r_monthly
                * (1 + r_monthly) ** n
            ) / (
                (1 + r_monthly) ** n - 1
            )

            return f"Monthly EMI: ₹{emi:.2f}"

        return str(eval(expression))

    except Exception as e:

        return f"Calculator Error: {e}"


@tool
def stock_price(symbol: str) -> str:
    """
    Retrieve stock price using Alpha Vantage.
    """

    if not ALPHA_VANTAGE_API_KEY:

        return (
            "Alpha Vantage API key not configured."
        )

    try:

        url = (
            "https://www.alphavantage.co/query"
            f"?function=GLOBAL_QUOTE"
            f"&symbol={symbol}"
            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )

        response = requests.get(url)

        data = response.json()

        if (
            "Global Quote" in data
            and data["Global Quote"]
        ):

            price = float(
                data["Global Quote"]["05. price"]
            )

            return (
                f"{symbol}: ${price:.2f}"
            )

        return (
            f"No stock data found for {symbol}"
        )

    except Exception as e:

        return f"Stock Error: {e}"


# ==================================================
# FINANCE AGENT
# ==================================================

class FinanceAgent:

    def __init__(self):

        self.memory = {}

        self.tools = [
            calculator,
            stock_price
        ]

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.15
        )

        self.llm_with_tools = (
            self.llm.bind_tools(
                self.tools
            )
        )

        self.system_prompt = """
You are MyGenius AI Financial Agent.

You specialize in:

- Personal finance
- Investments
- Stock market analysis
- EMI calculations
- Financial planning

Tool Selection Rules:

- Simple calculations -> calculator
- EMI calculations -> calculator
- Stock prices -> stock_price

Always provide a clear final answer.
"""

    # =====================================
    # Invoke
    # =====================================

    def invoke(
        self,
        query: str,
        session_id: str = "default"
    ) -> str:

        try:

            if session_id not in self.memory:

                self.memory[session_id] = []

            messages = [
                SystemMessage(
                    content=self.system_prompt
                )
            ]

            messages.extend(
                self.memory[session_id]
            )

            messages.append(
                HumanMessage(
                    content=query
                )
            )

            response = self.llm_with_tools.invoke(
                messages
            )

            # Tool call handling
            if response.tool_calls:

                tool_outputs = []

                for call in response.tool_calls:

                    tool_name = call["name"]
                    tool_args = call["args"]

                    for tool_obj in self.tools:

                        if tool_obj.name == tool_name:

                            result = tool_obj.invoke(
                                tool_args
                            )

                            tool_outputs.append(
                                f"{tool_name}: {result}"
                            )

                final_prompt = messages + [
                    AIMessage(
                        content=
                        f"Tool Results:\n{tool_outputs}"
                    )
                ]

                final_response = self.llm.invoke(
                    final_prompt
                )

                answer = (
                    final_response.content
                )

            else:

                answer = response.content

            self.memory[session_id].append(
                HumanMessage(
                    content=query
                )
            )

            self.memory[session_id].append(
                AIMessage(
                    content=answer
                )
            )

            return answer

        except Exception as e:

            return (
                f"Finance Agent Error: {e}"
            )

    # =====================================
    # Clear Memory
    # =====================================

    def clear_memory(
        self,
        session_id: str
    ):

        if session_id in self.memory:

            del self.memory[session_id]


# ==================================================
# Local Testing
# ==================================================

if __name__ == "__main__":

    agent = FinanceAgent()

    while True:

        query = input("\nUser: ")

        if query.lower() == "exit":
            break

        response = agent.invoke(
            query,
            session_id="test_user"
        )

        print("\nAssistant:", response)
