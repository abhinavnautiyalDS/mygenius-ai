# from langchain_groq import ChatGroq

# from langchain_google_genai import (
#     ChatGoogleGenerativeAI
# )

# from langchain_huggingface import (
#     HuggingFaceEndpoint,
#     ChatHuggingFace
# )

# from langchain_openai import (
#     ChatOpenAI
# )

# from config.settings import *


# class LLMFactory:

#     @staticmethod
#     def get_chatbot_llm():

#         endpoint = HuggingFaceEndpoint(
#             repo_id=
#             "Qwen/Qwen2.5-7B-Instruct",
#             huggingfacehub_api_token=
#             HF_TOKEN
#         )

#         return ChatHuggingFace(
#             llm=endpoint
#         )

#     @staticmethod
#     def get_finance_llm():

#         return ChatGroq(
#             model_name=
#             "llama-3.3-70b-versatile",
#             groq_api_key=
#             GROQ_API_KEY
#         )

#     @staticmethod
#     def get_rag_llm():

#         return ChatGoogleGenerativeAI(
#             model="gemini-2.0-flash",
#             google_api_key=
#             GOOGLE_API_KEY
#         )

#     @staticmethod
#     def get_sql_llm():

#         return ChatOpenAI(
#             model=
#             "nousresearch/hermes-3-llama-3.1-8b:free",
#             openai_api_base=
#             "https://openrouter.ai/api/v1",
#             openai_api_key=
#             OPENROUTER_API_KEY
#         )

#     @staticmethod
#     def get_summarizer_model():

#         return (
#             "mistralai/mistral-7b-instruct"
#         )

if api_key:
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key
    )
else:
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
