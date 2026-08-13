# RAG on Azure

A production-style Retrieval-Augmented Generation app: upload a PDF, ask
questions about it, get answers grounded in the document with page-level
sources.

- **Frontend:** React (Vite)
- **Backend:** FastAPI
- **Storage:** Azure Blob Storage (raw PDFs)
- **Vector/keyword search:** Azure AI Search
- **Embeddings + chat:** Azure OpenAI

## Project structure

```
RAG_AZURE_CHATBOT/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, CORS, router wiring
│   │   ├── config.py             # env-driven settings
│   │   ├── models.py             # request/response schemas
│   │   ├── routers/
│   │   │   ├── upload.py         # POST /api/upload
│   │   │   └── query.py          # POST /api/query
│   │   └── services/
│   │       ├── blob_storage.py   # upload PDF to Blob Storage
│   │       ├── pdf_processor.py  # text extraction + chunking
│   │       ├── openai_service.py # embeddings + chat completion
│   │       └── search_service.py # index + hybrid search in AI Search
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── components/
│   │   │   ├── UploadPDF.jsx
│   │   │   └── ChatBox.jsx
│   │   └── index.css
│   ├── package.json
│   └── .env.example
├── azure/
│   ├── search-index-schema.json  # AI Search index definition
│   ├── create_index.py           # script to create/update the index
│   └── deploy.md                 # ACR + Container Apps deployment steps
└── README.md
```

## Request and ingestion flow

**Ingestion (upload):**
1. User uploads a PDF in the React UI → `POST /api/upload` (multipart).
2. FastAPI uploads the original PDF bytes to Azure Blob Storage, generating a
   `document_id` (UUID) and blob path `document_id/filename.pdf`.
3. `pypdf` extracts text per page.
4. Page text is split into overlapping chunks (`CHUNK_SIZE` / `CHUNK_OVERLAP`),
   each chunk keeping its source page number.
5. Each chunk is embedded via the Azure OpenAI **embedding** deployment.
6. Chunks + vectors + metadata (`document_id`, `filename`, `page`) are upserted
   into Azure AI Search.
7. Response returns `document_id`, filename, and chunk count to the UI.

**Query (ask a question):**
1. User types a question → `POST /api/query` with `{ question, document_id }`.
2. FastAPI embeds the question with the **same** embedding deployment used for
   ingestion.
3. A hybrid search (BM25 keyword + vector) runs against Azure AI Search,
   optionally filtered to the uploaded `document_id`, returning the top-K chunks.
4. The question + retrieved chunk text are sent to the Azure OpenAI **chat**
   deployment with a system prompt constraining it to answer only from the
   provided excerpts.
5. The generated answer, plus the source chunks (filename, page, excerpt,
   score), are returned to the UI and rendered under the assistant's reply.

## Local setup

### Prerequisites
- Python 3.11+
- Node 18+
- An Azure OpenAI resource with a **chat** deployment and an **embedding**
  deployment (e.g. `gpt-4o-mini` and `text-embedding-3-small`)
- An Azure AI Search service
- An Azure Storage account

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env        # Windows: copy, macOS/Linux: cp
# edit .env with your real Azure values
```

Create the Azure AI Search index (one-time):

```bash
python ../azure/create_index.py
```

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Docs available at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
copy .env.example .env        # set VITE_API_BASE_URL if not localhost:8000
npm run dev
```

Open `http://localhost:5173`, upload a PDF, and ask questions.

### 3. Docker (backend only)

```bash
cd backend
docker build -t rag-backend .
docker run -p 8000:8000 --env-file .env rag-backend
```

## Azure deployment

See [`azure/deploy.md`](azure/deploy.md) for step-by-step Azure CLI commands
to push the backend image to Azure Container Registry and deploy it on Azure
Container Apps, plus a note on deploying the frontend.

## Environment variables

All Azure configuration is read from environment variables — see
[`backend/.env.example`](backend/.env.example) and
[`frontend/.env.example`](frontend/.env.example). Nothing is hardcoded;
placeholders like `<AZURE_OPENAI_ENDPOINT>` must be replaced with your actual
resource values before running.
