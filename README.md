# Automated Software Architecture Solution (ASAC)

ASAC is an intelligent, multi-agent AI system designed to transform natural language user requirements into comprehensive High-Level Design (HLD) software architecture specifications. Powered by specialized LLM agents and strict verification pipelines, ASAC guides users through requirement discovery, cross-validates constraints, designs rich architecture diagrams, conducts security audits, and provides a RAG-powered, strictly guarded chat assistant over generated project specifications.

---

## 🏗️ Architecture & Multi-Agent Pipeline Overview

ASAC executes a sequential multi-agent workflow where each specialized agent focuses on a distinct stage of system architecture design:

```mermaid
flowchart TD
    User([User]) --> UI[React Frontend]
    UI --> API[FastAPI Backend]
    
    subgraph Multi-Agent Pipeline
        API --> Agent1[1. Requirements Discovery Agent]
        Agent1 -->|Interactive Q&A / Clarifications| UI
        Agent1 -->|Discovered State| Agent2[2. Requirement Specification Agent]
        Agent2 -->|Validates Constraints & Removes Duplicates| Agent3[3. Architecture Design Agent]
        Agent3 -->|Detailed Mermaid & Cloud Topology| Agent4[4. Security Audit Agent]
        Agent4 -->|STRIDE / OWASP Threat Model| Agent5[5. Documentation Agent]
        Agent5 -->|Consolidated HLD Markdown| DB[(SQLite Storage)]
    end

    subgraph Knowledge & Context
        DB --> VectorDB[Chroma Vector Store / RAG Engine]
        VectorDB --> GuardedChat[Context-Guarded Chat Assistant]
        UI --> GuardedChat
    end
```

### Specialized Agents Overview

1. **Requirements Discovery Agent**:
   - Interactively queries users on technical boundaries (e.g., target users, throughput, storage, compliance).
   - Dynamically checks for completeness before proceeding.

2. **Requirement Specification Agent**:
   - Cross-validates constraints to resolve contradictions (e.g., ensuring functional user capacity aligns with performance SLA metrics).
   - Deduplicates requirements and categorizes them into Functional, Non-Functional, Technical, and Integration specifications.

3. **Architecture Design Agent**:
   - Generates comprehensive architectural patterns, microservice boundaries, data flow strategies, and trade-offs.
   - Output includes detailed, multi-tier Mermaid diagrams showcasing cloud infrastructure components (e.g., Load Balancers, API Gateways, Microservices, Caching tiers, Managed DBs, Messaging queues).

4. **Security Audit Agent**:
   - Conducts threat modeling (STRIDE framework) and identifies security controls, encryption requirements, and compliance policies.

5. **Documentation Agent**:
   - Aggregates all upstream outputs into a clean, standard High-Level Design (HLD) document.

---

## ✨ Key Features

- **Strict Context-Guarded Chat Assistant**:
  - Embedded RAG chat assistant that answers queries strictly based on the generated HLD document and project context.
  - Automatically rejects off-topic queries (e.g., general math, general knowledge, coding trivia) with a helpful guardrail refusal.
- **Resumable Execution Pipeline**:
  - Supports resilient state persistence allowing users to resume failed or paused pipeline steps without losing progress.
- **Fixed & Responsive Chat Workspace**:
  - Full-height viewport UI with clean inner message scrolling for history navigation.
- **Export & Report Generation**:
  - Download or export complete High-Level Design documentation as formatted Markdown files.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLite, ChromaDB / RAG Engine, LangChain / OpenAI / Azure OpenAI / Ollama LLMs.
- **Frontend**: React, Vite, TailwindCSS, Lucide Icons, Mermaid.js (rendering system diagrams dynamically).

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm
- Access to an AI Provider (Azure OpenAI, OpenAI, or local Ollama)

---

### 2. Backend Configuration & Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Environment Variables (`backend/.env`)

Copy `backend/.env.example` to `backend/.env` and configure all required variables:

```bash
cp .env.example .env
```

Here is the complete reference of all backend environment variables:

```env
# ==============================================================================
# 1. AI Provider Selection
# Options: "azure_openai", "openai", "ollama"
# ==============================================================================
AI_PROVIDER=azure_openai

# ==============================================================================
# 2. Azure OpenAI Configuration (Required if AI_PROVIDER="azure_openai")
# ==============================================================================
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# ==============================================================================
# 3. Standard OpenAI Configuration (Required if AI_PROVIDER="openai")
# ==============================================================================
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# ==============================================================================
# 4. Ollama Configuration (Required if AI_PROVIDER="ollama")
# ==============================================================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# ==============================================================================
# 5. Database & Persistence Configuration
# ==============================================================================
# SQLite database URL (default). For Postgres: postgresql://user:pass@host:port/dbname
DATABASE_URL=sqlite:///./data/asac.db

# ==============================================================================
# 6. Pipeline Execution & Timeouts
# ==============================================================================
# Fallback to hardcoded mock templates if AI agent calls fail (Set to true only for offline testing)
TEMPLATE_FALLBACK=false

# Maximum response timeout in seconds per individual agent call
AGENT_TIMEOUT=60

# Full multi-agent pipeline timeout limit in seconds
PIPELINE_TIMEOUT=180

# Maximum token generation cap per agent call
MAX_TOKENS=950

# ==============================================================================
# 7. RAG Knowledge Base & Context Retrieval
# ==============================================================================
# Number of top matching vector chunks to retrieve for RAG context queries
RAG_TOP_K=5

# Relative or absolute directory containing reference knowledge docs
KNOWLEDGE_DIR=knowledge

# ==============================================================================
# 8. Security & CORS Configuration
# ==============================================================================
# Comma-separated list of allowed frontend origins for CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost
```

#### Running the Backend Server

```bash
# Run FastAPI server with Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
The backend API documentation will be available at `http://localhost:8000/docs`.

---

### 3. Frontend Configuration & Setup

```bash
# Navigate to frontend directory
cd frontend

# Install packages
npm install
```

#### Environment Variables (`frontend/.env`)

Copy `frontend/.env.example` to `frontend/.env`:

```bash
cp .env.example .env
```

```env
# Base URL for Backend API requests
VITE_API_URL=http://localhost:8000/api/v1
```

#### Running the Frontend Application

```bash
npm run dev
```
The React frontend application will be live at `http://localhost:5173`.

### 4. Engineering Quality Notes

#### Scalability and operational design

- The analysis pipeline runs agents sequentially so each stage can consume validated output from the previous stage.
- Each agent has an independent timeout and failure boundary; completed analyses can resume missing stages.
- Database persistence separates analysis metadata, generated outputs, uploaded documents, vector chunks, and chat history.
- RAG retrieval is bounded by `RAG_TOP_K`; chat context is limited to the most recent six messages to keep latency and prompt size predictable.
- For production scale, move SQLite to PostgreSQL, place uploaded documents and vectors in managed storage, and run pipeline jobs through a queue instead of an in-process request.

#### Functional boundaries and limitations

- The system generates architecture guidance and documentation; it does not provision cloud resources or execute deployment changes.
- AI responses are grounded in the stored analysis outputs and retrieved project documents. Missing decisions are reported as unspecified rather than invented.
- Default limits are 2 uploaded documents per discovery request, 2 MB per document, 4,000 characters per chat message, and 60 seconds per agent call.
- Generated architecture recommendations require human review before implementation, security approval, or compliance sign-off.

#### Testing and observability

The implementation supports positive and negative checks for request validation, provider selection, AI failure handling, JSON parsing, template fallback, session lookup, off-topic refusal, RAG retrieval, and resumable pipeline stages. Backend events use standard Python logging and record provider, agent, session, and retrieval metadata without recording API keys or chat content.

Run the available static validation from `backend`:

```powershell
.\.venv\Scripts\python.exe -m compileall app
```

#### Configuration and secrets

Copy `.env.example` to `.env` for local setup. `.env` files, virtual environments, dependency directories, databases, and build output are excluded by `.gitignore`. Provider credentials are validated at startup and must be supplied through environment variables; never commit real keys or include them in logs.

---

## 📄 License & Summary

ASAC simplifies software architecture design by combining multi-agent verification, robust LLM guardrails, and dynamic system modeling into a seamless web workspace.
