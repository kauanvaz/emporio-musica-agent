# Empório da Música — AI Customer Service Agent

A text-based customer service agent for **Empório da Música**, a fictional musical instrument store in Campo Grande/MS, Brazil. The agent answers questions about products, stock, orders, promotions and store policies, using a hybrid Retrieval-Augmented Generation (RAG) + Text-to-SQL architecture.

Built with **Python**, **LangChain**, and **Streamlit**, packaged with **Docker**.

---

## Features
- Conversational agent that decides, per message, whether to answer directly or call a tool.
- **Text-to-SQL** over structured data (products, orders, customers, promotions in CSVs).
- **RAG** over a PDF manual of store policies (returns, payment, hours, shipping).
- **Multi-turn context** kept in the Streamlit session.
- **Web UI** (Streamlit).
- **Docker** packaging.

---

## Tech stack

- **Python 3.14**
- **LangChain** (`create_agent` / function calling) + **LangGraph**
- **OpenAI** (chat: `gpt-4o-mini`, embeddings: `text-embedding-3-small`)
- **FAISS** (vector index) + **pypdf** (PDF parsing)
- **SQLite** (in-memory, from CSVs) + **pandas**
- **Streamlit** (web UI)
- **uv** (dependency management, lockfile) · **pytest** · **Docker**

---

## Getting started

### 1. Install Docker

The application runs easily through **Docker**, so that's the only requirement besides your OpenAI key.

- **Official documentation (choose your OS):**
  - [Install Docker Engine (Linux)](https://docs.docker.com/desktop/setup/install/linux/)
  - [Install Docker Desktop (macOS)](https://docs.docker.com/desktop/setup/install/mac-install/)
  - [Install Docker Desktop (Windows)](https://docs.docker.com/desktop/setup/install/windows-install/)

- **Tip for first-timers:** if you are new to containers, the official
  [Docker quickstart tutorials](https://docs.docker.com/get-started/) are the best
  starting point.

Verify the installation is working:
```bash
docker --version
docker compose version
```

### 2. Get the code
```bash
git clone <repo-url>
cd emporio-musica-agent
```

### 3. Configure the environment
```bash
# Create your environment file
cp .env.example .env
# Edit .env and set your OpenAI API key
```
```dotenv
OPENAI_API_KEY=your_o...here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### 4. Build and run with Docker Compose
```bash
docker compose up --build
```

### 5. Open the Web UI
- Go to **http://localhost:8501**

### 6. Stop the services
```bash
docker compose down
```

---

## Project structure
```
.
├── data/              # Source data: CSVs + policies PDF
├── src/
│   ├── agent.py       # Agent orchestration (create_agent) + system prompt
│   ├── tools.py       # Tools exposed to the LLM (SQL, search, RAG)
│   ├── database.py    # CSV → SQLite + safe SQL execution
│   └── rag.py         # PDF → vector index (FAISS) with disk cache
├── tests/             # pytest suite (database + RAG)
├── app.py             # Streamlit web UI
├── main.py            # CLI
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml     # Dependencies (uv)
```

---

## Tests
- `tests/test_database.py` — CSV→SQLite conversion and **SQL defenses** (blocks `DELETE`, `DROP`, multiple statements).
- `tests/test_rag.py` — policy index build and retrieval.

```bash
uv run pytest -v
```

---

## Technical decisions

### Why LangChain (`create_agent`)
The current LangChain harness (`create_agent`, built over LangGraph) natively supports the **ReAct / tool-calling loop**. It frees me from hand-rolling the model→tool→model loop and conversation management, while keeping full control over the tools and prompt.

### Why a hybrid RAG + Text-to-SQL architecture
The challenge provides two fundamentally different data natures:
- **Structured data** (CSVs) → a relational model and **Text-to-SQL** is the right tool.
- **Unstructured policies** (PDF) → **Retrieval-Augmented Generation** retrieves the relevant text snippets before answering.

Keeping them as separate, specialized tools avoids forcing either source into the wrong mechanism and gives deterministic answers where it matters (prices, stock).

### Why OpenAI
A single, well-supported provider keeps the setup simple and predictable. `gpt-4o-mini` is a good cost/latency trade-off for a text assistant, and `text-embedding-3-small` powers the policy retrieval.

### Why dedicated tools for catalog search (`search_products`)
The LLM, writing SQL from scratch, struggled with terms that live in the **category**, not in the product name (e.g. "violão" is a category, not in *"Yamaha C40"*). A dedicated deterministic tool searches **name + description + category** and returns only in-stock items, removing hallucinations and fragile hand-written SQL for this domain.

### Why defense in code for SQL
A Text-to-SQL agent depends on the LLM's output, but we don't trust it blindly. Every generated query is sanitized (dialect fixes) and **write/destructive commands are blocked** (`INSERT`, `UPDATE`, `DELETE`, `DROP`, multiple statements). The DB is read-only and in-memory, so even a rogue prompt can't corrupt anything.

### Why RAG text normalization
The PDF parser (`pypdf`) often splits words across lines, degrading embedding retrieval. Extracted text is normalized before chunking, which improved retrieval of cover metadata (address, phone) — a real bug found during testing.

### Why Streamlit
Python-native and low-friction: it exposes the same `interact_with_agent` in a web UI in a handful of lines, with built-in chat widgets and session state. It keeps the focus on the agent, not the frontend.

### Why Docker + uv
`uv` with a committed lockfile (`uv.lock`) makes the environment reproducible. Docker packages the app so it runs identically anywhere, with one exposed port and a simple `docker compose up`.

---

## Known limitations & next steps

Given the time available, some improvements were consciously deferred:

- **Automation** — Build a monitoring system to retrain embeddings or fine-tune the LLM as new data arrives.
- **End-to-end agent tests** — the current suite covers the database and RAG layers, but not full agent conversations (they require a live API key and are costlier).
- **Redis as conversation store** — today the history is kept in the Streamlit session, which is lost on restart/deploy. A **Redis** store (by `session_id`, with TTL) would make history durable and the app truly stateless — the standard production pattern for agents with memory.
- **`active_promotions` tool** — a dedicated tool to list active promotions with the product name. Currently promotions are answered through generic SQL, and the answer may not always name the specific product.
- **More robust PDF parsing** — for unusual layouts / scanned pages, a more advanced PDF extractor or OCR would improve retrieval.

---

## AI-assisted development

This project was developed with support from an **AI coding assistant** — the assistant of **OpenCode Go** (`opencode go`, running with DeepSeek V4 Flash).

How it was used:

- **Writing the test suite**: drafting the pytest tests for the database (SQL defenses) and the RAG layer.
- **Building the Streamlit web app**: generating the chat UI and wiring it to the agent's interact_with_agent, including maintaining multi-turn history in the session.
- **Prompt design**: I asked the assistant for help creating the agent's **system prompt**, passing all the necessary information about the store, the agent's role and the available tools, and guiding the final structure of the prompt into these sections:
  - **Store identity** (identity of the store),
  - **How to work** (the agent's behavior and rules),
  - **Tool-routing flow** (which tool to use for each kind of question),
  - **Return and exchange rules** (summarized for quick reference),
  - **Database tables** (the schema reference injected into the prompt — the list is included below),
  - **Important** section with the final details (language, currency format, asking for missing info, and not promising unverified conditions).
- **Documentation**: drafting this README, including the technical justifications and the run instructions. The technical decisions described here follow the ones I recorded in docs/decisions.md, which tracks each decision and the issues found during testing.