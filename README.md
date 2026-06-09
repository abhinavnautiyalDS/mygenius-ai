# 🚀 MyGenius AI

<img width="1889" height="872" alt="image" src="https://github.com/user-attachments/assets/2ca56328-d602-4e34-8ade-1eaa6d1c7db7" />

### A Unified Multi-Agent Generative AI Platform

**MyGenius AI** is a production-inspired multi-agent AI system that intelligently routes user requests to specialized AI agents through a centralized orchestration layer.

Instead of building isolated AI applications such as a chatbot, document summarizer, or RAG system, the goal of this project was to create a unified platform capable of understanding user intent and automatically selecting the most appropriate agent for the task.

The project evolved from an earlier Financial GenAI Assistant into a scalable architecture focused on orchestration, maintainability, routing, and multi-agent collaboration.

---

# 📖 Project Motivation

Most GenAI portfolio projects stop at:

- Chatbots
- RAG systems
- PDF summarizers
- SQL assistants

While these systems demonstrate specific capabilities, they often operate independently.

During the development of my previous Financial GenAI Assistant, I realized a fundamental limitation:

> The user had to decide which AI capability to use instead of the system understanding the user's intent and making that decision automatically.

This project was built to solve that problem.

The objective was not to build another chatbot.

The objective was not to build another RAG application.

The objective was not to build another finance assistant.

The objective was to build a system capable of coordinating multiple AI capabilities through a single interface.

---

# 🎯 Project Goals

### Build a Unified AI Platform

Create a centralized system where multiple AI agents can coexist and collaborate.

### Implement Intelligent Routing

Automatically identify user intent and route requests to specialized agents.

### Improve Maintainability

Separate:

- UI
- API Layer
- Routing Logic
- Agents
- Tools
- Data Storage

into independent modules.

### Create a Production-Oriented Architecture

Move beyond notebook-based demos and implement an architecture that resembles real-world AI systems.

---

# 🏗️ System Architecture

```text
User
 │
 ▼
Streamlit UI
 │
 ▼
FastAPI Backend
 │
 ▼
Router
 │
 ▼
Intent Classification
 │
 ├── Chatbot Agent
 │
 ├── Finance Agent
 │
 ├── SQL Agent
 │
 ├── RAG Agent
 │
 └── Summarizer Agent
 │
 ▼
Response
```

---

# ⚙️ Technology Stack

## Frontend

- Streamlit

## Backend

- FastAPI

## LLM Framework

- LangChain

## Workflow Orchestration

- LangGraph (Planned Expansion)

## Language Models

- Gemini 2.5 Flash

## Embeddings

- Gemini Embeddings

## Vector Database

- FAISS

## Database

- SQLite

## Programming Language

- Python

---

# 🧠 Why Gemini?

The project initially experimented with multiple providers:

- Hugging Face
- Groq
- OpenRouter
- Gemini

Managing multiple providers increased complexity significantly.

The architecture was eventually standardized on Gemini because of:

✅ Fast inference

✅ Free developer tier

✅ Large context window

✅ Easy LangChain integration

✅ Simplified deployment

✅ Single-provider maintenance

Final architecture:

```text
Router
   └── Gemini 2.5 Flash

Chatbot Agent
   └── Gemini 2.5 Flash

Finance Agent
   └── Gemini 2.5 Flash + Tools

RAG Agent
   └── Gemini 2.5 Flash

SQL Agent
   └── Gemini 2.5 Flash

Summarizer Agent
   └── Gemini 2.5 Flash

Embeddings
   └── Gemini Embeddings
```

---

# 🔀 Routing System

The router acts as the brain of the platform.

Its responsibility is determining:

```text
User Query
     ↓
Intent Detection
     ↓
Agent Selection
     ↓
Response
```

---

## Why Not LLM-Based Routing?

Many multi-agent systems use an LLM router.

Example:

```text
User Query
      ↓
LLM Router
      ↓
Agent
      ↓
Response
```

While flexible, this approach introduces:

- Additional latency
- Extra API costs
- Non-deterministic behavior
- Debugging complexity

---

## Heuristic-Based Routing

MyGenius AI uses deterministic routing rules.

Examples:

```python
if pdf_uploaded and "summarize" in query:
    route = "summarizer"

elif pdf_uploaded:
    route = "rag"

elif contains_financial_keywords(query):
    route = "finance"

elif contains_sql_keywords(query):
    route = "sql"

else:
    route = "chatbot"
```

Benefits:

-  Faster
-  Cheaper
-  Predictable
- Easier Debugging
- Production Friendly

---

# 🤖 Agent Architecture

## 1. Chatbot Agent

### Purpose

General conversational AI.

### Responsibilities

- Answer general questions
- Explain concepts
- Assist learning
- Handle conversations outside specialized domains

### Example Queries

```text
What is Machine Learning?

Explain Neural Networks

How does Inflation work?
```

---

## 2. Finance Agent

### Purpose

Handle financial intelligence tasks.

### Responsibilities

- Financial explanations
- Investment concepts
- Financial calculations
- Market-related queries

### Example Queries

```text
What is SIP?

Compare SIP vs FD

How is EMI calculated?

Explain Compound Interest
```

### Architecture

```text
User Query
      ↓
Finance Agent
      ↓
Gemini
      ↓
Finance Tools
      ↓
Response
```

---

## 3. RAG Agent

### Purpose

Answer questions from uploaded documents.

### Why RAG?

LLMs cannot reliably answer questions about private documents they have never seen.

RAG provides document-grounded responses.

### Pipeline

```text
PDF Upload
      ↓
Text Extraction
      ↓
Chunking
      ↓
Embeddings
      ↓
FAISS Vector Store
      ↓
Similarity Search
      ↓
Retrieved Context
      ↓
Gemini
      ↓
Answer
```

### Components

#### Document Loader

Extracts content from PDFs.

#### Chunking

Splits large documents into manageable sections.

#### Embeddings

Converts chunks into vector representations.

#### FAISS

Stores vectors for efficient retrieval.

#### Retriever

Finds the most relevant chunks.

#### Generator

Uses Gemini to generate grounded responses.

### Example Query

```text
What was the company's net income?
```

---

# 📄 4. Summarizer Agent

### Purpose

Summarize long-form documents.

### Architecture

```text
Document
     ↓
Text Extraction
     ↓
Chunking
     ↓
Chunk Summaries
     ↓
Summary Aggregation
     ↓
Final Summary
```

### Why Hierarchical Summarization?

Large documents often exceed context limits.

Instead of summarizing the entire document at once:

```text
Document
     ↓
Chunk 1 Summary

Chunk 2 Summary

Chunk 3 Summary
     ↓
Merged Summary
     ↓
Final Summary
```

This improves scalability and summary quality.

### Example Query

```text
Summarize this annual report.
```

---

# 🗄️ 5. SQL Agent

### Purpose

Bridge natural language and structured databases.

### Architecture

```text
User Question
      ↓
Gemini
      ↓
SQL Query Generation
      ↓
SQLite Database
      ↓
Query Results
      ↓
Natural Language Response
```

### Example Queries

```text
Show total revenue.

Find top customers.

Average monthly sales.
```

---

# 📁 Project Structure

```text
mygenius-ai/
│
├── agents/
│   ├── chatbot_agent.py
│   ├── finance_agent.py
│   ├── rag_agent.py
│   ├── sql_agent.py
│   └── summarizer_agent.py
│
├── router/
│   ├── intent_classifier.py
│   └── routing_logic.py
│
├── api/
│   └── app.py
│
├── ui/
│   └── streamlit_app.py
│
├── config/
│   ├── settings.py
│   └── prompts.py
│
├── tools/
│   ├── calculator.py
│   ├── web_search.py
│   ├── stock_price.py
│   └── python_tool.py
│
├── memory/
│
├── data/
│   ├── documents/
│   ├── vectorstore/
│   └── sqlite/
│
├── requirements.txt
│
├── README.md
│
└── .env
```

---

# 🚧 Engineering Challenges

## Challenge 1: Agent Integration

Each module originally worked independently.

The challenge was designing a unified orchestration layer.

---

## Challenge 2: Routing Accuracy

Incorrect routing causes poor user experience.

Multiple routing iterations were required.

---

## Challenge 3: Dependency Conflicts

Examples:

- LangGraph package mismatches
- Deprecated APIs
- Version conflicts

---

## Challenge 4: Multi-Provider Complexity

Managing:

- Hugging Face
- Groq
- OpenRouter
- Gemini

created unnecessary complexity.

This led to model standardization.

---

## Challenge 5: State Management

Managing:

- Session IDs
- Chat History
- Memory
- Agent Context

became increasingly important.

---

# 📈 Key Learnings

This project taught me that:

Building AI features is relatively straightforward.

Building AI systems is much harder.

Important engineering challenges include:

- Routing
- State Management
- Tool Integration
- Architecture Design
- Scalability
- Maintainability
- Deployment

The most valuable lessons came from system design rather than prompt engineering.

---

# 🔮 Future Improvements

## LangGraph Integration

Introduce graph-based workflows.

```text
Router
   ↓
Planner
   ↓
Agent Chain
   ↓
Response
```

---

## Multi-Agent Collaboration

Example:

```text
Finance Agent
      ↓
SQL Agent
      ↓
Summarizer Agent
      ↓
Final Report
```

---

## Shared Memory

Persistent memory across agents.

---

## Agent Planning

Dynamic task decomposition.

---

## Portfolio Analytics

Advanced financial intelligence workflows.

---

## Autonomous Research Workflows

Multi-step reasoning and execution.

---

# 📸 Screenshots

## Main Dashboard
https://github.com/user-attachments/assets/a9ebdf4c-d48d-45dc-a9fc-0272df014d5e

---

## Router Logs

<img width="1075" height="860" alt="Screenshot 2026-06-08 150916" src="https://github.com/user-attachments/assets/eff6ce26-b065-4aaf-bbc7-e26b805558e2" />

---

## FastAPI Swagger
<img width="1920" height="1540" alt="image" src="https://github.com/user-attachments/assets/dcbea860-e625-4ed1-a9d5-8f3209753971" />

---



# 👨‍💻 Author

**Abhinav Nautiyal**

Physics Graduate →  Data Scientist → GenAI Builder

Passionate about:

- Generative AI
- Machine Learning
- Multi-Agent Systems
- RAG Architectures
- AI System Design

---

# ⭐ If you found this project interesting

Consider giving the repository a star and connecting with me on LinkedIn.

**MyGenius AI is not just a chatbot project.**

It is an exploration of how multiple AI capabilities can be orchestrated into a unified intelligent system.
