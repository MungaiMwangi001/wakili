# Wakili: RAG-Driven Legal Intelligence

A high-performance, locally deployable legal document analyzer built for researchers and legal professionals. Features specialized Swahili support and a full Retrieval-Augmented Generation pipeline using open-source models.

---

## Key Features

- **RAG-Driven Audit Mode** — Deep-dive analysis that cites specific clauses and legal sections.
- **Structured Intelligence** — Returns more than just text: extracts risk flags, actionable obligations, and source citations.
- **Bilingual Core** — Native support for English and Swahili with automatic language detection.
- **Knowledge Base Fallback** — When document confidence is low, Wakili falls back to a pre-loaded Kenyan law knowledge base covering the Employment Act 2007, Contract Act Cap 23, Consumer Protection Act 2012, and Land Act 2012.
- **Conversation Memory** — Supports follow-up questions within a session. Previous turns are passed to the LLM so users can ask "what about clause 5?" after an initial answer.
- **Privacy First** — Designed to run locally. Document embeddings are generated on-device using sentence-transformers. LLM generation uses the Groq API (free tier) with no document data stored externally.
- **High-Contrast UI** — Modern, accessible interface designed for clarity and rapid document auditing.

---

## System Architecture

```
wakili/
├── backend/                    # FastAPI + RAG engine
│   ├── app/
│   │   ├── api/                # Routers: auth, documents, ask, metrics
│   │   ├── core/               # Config, security (JWT + bcrypt), database
│   │   ├── models/             # SQLAlchemy ORM: User, Document, Query
│   │   ├── schemas/            # Pydantic v2 request/response schemas
│   │   ├── services/           # GroqService, EmbeddingService, VectorStore,
│   │   │                       # RAGPipeline, Chunker, TextExtractor
│   │   └── utils/              # Language detection, auth dependencies
│   ├── knowledge_base/         # Drop Kenyan law PDFs here for KB indexing
│   ├── scripts/
│   │   ├── load_knowledge_base.py   # Pre-loads legal KB into ChromaDB
│   │   ├── evaluate.py              # ROUGE + Precision@K evaluation
│   │   └── init_db.py               # Database table creation
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js 14 (App Router)
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   ├── components/         # AppShell, ChatBubble, RiskBadge
│   │   ├── hooks/              # useTranslation
│   │   ├── i18n/               # English and Swahili UI strings
│   │   ├── lib/api.ts          # Typed Axios client
│   │   └── store/              # Zustand global state (language, session)
│   └── Dockerfile
├── docker-compose.yml          # Orchestration: PostgreSQL, ChromaDB, Redis,
│                               # Backend, Frontend
└── .env.example
```

---

## The RAG Pipeline

Wakili uses a multi-stage retrieval process to ensure legal accuracy.

**Stage 1 — Ingestion**
PDF, DOCX, and TXT files are extracted, cleaned, and chunked using a token-aware splitter (tiktoken, 800-token chunks with 100-token overlap). Each chunk is embedded locally using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, CPU-friendly) and indexed into ChromaDB with cosine similarity.

**Stage 2 — Retrieval**
On each query, the question is embedded using the same model. ChromaDB performs a top-K=5 cosine similarity search across the user's documents. Each result includes a relevance score. If the best score falls below the confidence threshold (default: 0.35), the system falls back to the pre-loaded Kenyan law knowledge base rather than generating an unsupported answer.

**Stage 3 — Augmentation**
Retrieved chunks are assembled into a structured context block. The conversation history (last 6 turns) is prepended to the message list, enabling coherent follow-up questions within a session.

**Stage 4 — Generation**
Groq API (Llama 3.3 70B, free tier) processes the context through a specialized bilingual legal system prompt. The model is instructed to return structured JSON only.

**Stage 5 — Extraction**
The JSON response is parsed and returned to the client with the following fields:

| Field | Description |
|---|---|
| `answer` | Natural language response |
| `clause_summaries` | Per-clause plain-language summaries |
| `risk_flags` | Categorized risks with severity (low / medium / high) |
| `obligations` | Party-specific duties with conditions and deadlines |
| `retrieved_chunks` | Source citations with document title and chunk index |
| `used_knowledge_base` | Boolean indicating whether KB fallback was used |
| `disclaimer` | Legal disclaimer appended to every answer |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Authenticate and receive JWT |
| GET | `/auth/me` | Return current user profile |
| POST | `/documents/upload` | Upload and process a legal document |
| GET | `/documents/documents` | List all user documents |
| GET | `/documents/documents/{id}` | Get document details and analysis |
| DELETE | `/documents/documents/{id}` | Delete document and embeddings |
| POST | `/ask` | RAG Q&A with conversation history support |
| GET | `/metrics/metrics` | Usage statistics and response time analytics |
| GET | `/health` | Health check |

### Ask endpoint request body

```json
{
  "question": "What are my termination rights?",
  "document_id": 3,
  "language": "en",
  "conversation_history": [
    {"role": "user", "content": "Summarise the payment obligations."},
    {"role": "assistant", "content": "The contract requires payment within 30 days..."}
  ]
}
```

If `document_id` is omitted, Wakili searches across all of the user's uploaded documents. If `conversation_history` is omitted or empty, the query is treated as a standalone question.

---

## Swahili Support and Localization

Wakili is optimized for the East African legal context.

- **Heuristic detection** — Language detection combines `langdetect` with a curated Swahili keyword set (legal terms, common function words). A query matching two or more keywords is classified as Swahili without running the full detector, improving accuracy on short queries.
- **Bilingual system prompts** — Both English and Swahili system prompts are maintained separately. The Swahili prompt uses Kenyan legal Swahili terminology for risk type labels and severity levels.
- **Bilingual knowledge base** — Built-in KB entries are in English. Drop Swahili-language PDFs into `backend/knowledge_base/` and re-run `load_knowledge_base.py` to extend coverage.
- **Localized UI** — Full frontend strings are available in `src/i18n/` for English and Swahili. The language toggle is managed via Zustand global state.

---

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/your-username/wakili.git
cd wakili
cp .env.example .env
# Edit .env and set GROQ_API_KEY and SECRET_KEY

# 2. Launch the full stack
docker compose up --build

# 3. Load the legal knowledge base (run once after first build)
docker exec wakili-backend-1 python scripts/load_knowledge_base.py

# 4. Access the application
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8080/docs
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key (free at console.groq.com) | required |
| `GROQ_MODEL` | Groq model to use | `llama-3.3-70b-versatile` |
| `SECRET_KEY` | JWT signing secret (generate with `openssl rand -hex 32`) | required |
| `DATABASE_URL` | PostgreSQL connection string | set by docker-compose |
| `CHROMA_HOST` | ChromaDB host | `chromadb` |
| `CHROMA_PORT` | ChromaDB internal port | `8000` |
| `CONFIDENCE_THRESHOLD` | Min relevance score before KB fallback | `0.35` |
| `MAX_HISTORY_TURNS` | Conversation turns sent to LLM | `6` |
| `EMBEDDING_MODEL` | Sentence-transformers model | `all-MiniLM-L6-v2` |
| `CHUNK_SIZE` | Tokens per chunk | `800` |
| `CHUNK_OVERLAP` | Overlap between chunks | `100` |
| `TOP_K_RETRIEVAL` | Number of chunks retrieved per query | `5` |

---

## Knowledge Base

The knowledge base is a separate ChromaDB collection (`wakili_knowledge_base`) that is searched when user document retrieval confidence is low. It comes pre-loaded with summaries of the following Kenyan legislation:

- Employment Act 2007
- Law of Contract Act (Cap 23)
- Consumer Protection Act 2012
- Land Act 2012
- Common Kenyan contract risk flag reference

To add your own legal documents to the knowledge base, place PDF, DOCX, or TXT files in `backend/knowledge_base/` and run:

```bash
docker exec wakili-backend-1 python scripts/load_knowledge_base.py
```

This replaces the existing KB collection with a fresh index including all built-in entries plus your files.

---

## RAG Evaluation

The `scripts/evaluate.py` script measures retrieval and generation quality against a test set defined in `scripts/test_queries.jsonl`.

```bash
docker exec wakili-backend-1 python scripts/evaluate.py
```

Metrics reported:

| Metric | Description |
|---|---|
| Precision@K | Fraction of retrieved chunks that are relevant |
| Recall@K | Fraction of relevant chunks that were retrieved |
| ROUGE-1 | Unigram overlap between generated and reference answers |
| ROUGE-L | Longest common subsequence overlap |
| Avg response time | End-to-end latency in milliseconds |

---

## Security

- All API endpoints except `/auth/register`, `/auth/login`, and `/health` require a valid JWT in the `Authorization: Bearer` header.
- Passwords are hashed with bcrypt.
- Document uploads are scoped to the authenticated user. Users cannot access other users' documents.
- A legal disclaimer is appended to every generated answer: responses are AI-generated legal information, not legal advice.
- CORS origins are restricted to the values set in `ALLOWED_ORIGINS`.

---

## Design System

| Component | Token | Hex |
|---|---|---|
| Primary / brand | `bg-primary` | `#977dff` |
| Risk high | `text-rose-600` | `#e11d48` |
| Analysis panel | `bg-white` | `#ffffff` |
| App background | `bg-gray-50/30` | `#fafafa` |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11, SQLAlchemy (async), asyncpg |
| Database | PostgreSQL 16 |
| Vector store | ChromaDB 1.0 |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (local) |
| LLM | Groq API — Llama 3.3 70B Versatile (free tier) |
| Cache | Redis 7 |
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Framer Motion |
| State | Zustand |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Containerization | Docker, Docker Compose |

---

## Disclaimer

Wakili is a research and productivity tool. Responses are generated by an AI system and are not a substitute for advice from a qualified legal professional. Always consult a licensed advocate for decisions with legal consequences.