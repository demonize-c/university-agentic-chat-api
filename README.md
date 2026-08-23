# University Agentic Chat API 🎓🤖

An intelligent, retrieval-augmented generation (RAG) backend API and chat service designed for university support systems. Built with **FastAPI**, **LangChain**, **ChromaDB**, **HuggingFace Embeddings**, and **SQLAlchemy**.

---

## 🌟 Key Features

- **FastAPI Core**: High-performance RESTful API endpoints for asynchronous query processing.
- **RAG & Vector Retrieval**: LangChain integration with Chroma vector store for semantic document search.
- **HuggingFace Embeddings**: Open-source vector embeddings generation.
- **Relational Storage**: SQLAlchemy + PyMySQL integration for persistent data models.
- **Package Management**: Powered by `uv` for ultra-fast dependency management and virtual environment execution.

---

## 🚀 Getting Started

### Prerequisites

- Python `>= 3.14`
- [`uv`](https://github.com/astral-sh/uv) (Python package manager)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/demonize-c/university-agentic-chat-api.git
   cd university-agentic-chat-api
   ```

2. **Set up virtual environment & install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the project root:
   ```env
   HF_TOKEN=your_huggingface_token
   DATABASE_HOST=localhost
   DATABASE_PORT=3306
   DATABASE_USER=root
   DATABASE_PASSWORD=your_password
   DATABASE_NAME=university
   ```

---

## 🛠️ Usage

### Run Main Script
```bash
uv run app
```

### Run API Server
```bash
uv run api
```

Or using Uvicorn directly:
```bash
uv run uvicorn python_university_support_agent.main:app --reload
```

---

## 📂 Project Structure

```
university-agentic-chat-api/
├── src/
│   └── python_university_support_agent/
│       ├── db/          # Database connection & models
│       ├── retrieval/   # LangChain ChromaDB & embeddings retrieval
│       ├── routers/     # FastAPI routers & endpoints
│       ├── config.py    # Environment settings
│       ├── main.py      # Main entrypoint
│       └── cli.py       # CLI runner
├── .gitignore          # Git exclusion rules
├── pyproject.toml       # Project configuration
└── README.md            # Documentation
```

---

## 📄 License

Distributed under the MIT License.
