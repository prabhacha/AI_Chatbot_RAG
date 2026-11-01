# RAG AI Chatbot — React + Django + Gemini + FAISS

This project extends the basic React + Django chatbot with document upload, chunking, local embeddings, FAISS similarity search, and source-grounded Gemini answers.

## Backend setup (PowerShell)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-3.8-flash
```

`gemini-3.8-flash` is the model name suggested by the API error in the original chatbot. If Google AI Studio shows a different model available to your account, use that exact model ID.

Then run:

```powershell
python manage.py migrate
python manage.py runserver
```

## Frontend setup (second terminal)

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`.

## How to test
1. Upload a PDF, TXT, or MD file (maximum 10 MB).
2. Wait for indexing to finish. The first upload may take longer because `all-MiniLM-L6-v2` downloads on first use.
3. Ask a question answered by the document.
4. Expand **Sources used** to inspect retrieved chunks.

## API endpoints
- `GET /api/health/`
- `POST /api/documents/upload/` with multipart field `file`
- `GET /api/documents/`
- `DELETE /api/documents/<document_id>/`
- `POST /api/chat/` with JSON `{"message":"your question"}`

## RAG pipeline
PDF/TXT/MD → text extraction → overlapping chunks → local sentence-transformer embeddings → FAISS vector index → top-k retrieval → Gemini response with retrieved context.

## Notes
- This is a local learning demo, not a production security design.
- FAISS index and chunk metadata are stored in `backend/rag_data/` and can be rebuilt by deleting the documents in the UI and re-uploading them.
- Never put your Gemini key in React code or commit `.env`.
- If `faiss-cpu` or `sentence-transformers` won't install on your Python version, use a Python version supported by those packages (often 3.11/3.12) in a fresh virtual environment.
- Scanned PDFs with no selectable text need OCR before upload.
