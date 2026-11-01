import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API = "http://127.0.0.1:8000/api";

export default function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([{ role: "assistant", text: "Upload a PDF or TXT document, then ask me a question about it." }]);
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadDocuments() {
    try {
      const response = await axios.get(`${API}/documents/`);
      setDocuments(response.data.documents || []);
    } catch {
      setNotice("Cannot reach Django. Start the backend at http://127.0.0.1:8000.");
    }
  }
  useEffect(() => { loadDocuments(); }, []);

  async function uploadDocument(event) {
    event.preventDefault();
    if (!file) { setNotice("Please choose a PDF, TXT, or MD file first."); return; }
    const form = new FormData();
    form.append("file", file);
    setLoading(true);
    setNotice("Uploading, splitting, and indexing your document. The first run may take longer while the embedding model downloads.");
    try {
      const response = await axios.post(`${API}/documents/upload/`, form);
      setNotice(`${response.data.message} Added ${response.data.chunks_added} chunk(s).`);
      setFile(null);
      event.target.reset();
      await loadDocuments();
    } catch (error) {
      setNotice(error.response?.data?.error || "Upload failed. Check the Django terminal.");
    } finally { setLoading(false); }
  }

  async function deleteDocument(id) {
    setLoading(true);
    try { await axios.delete(`${API}/documents/${id}/`); setNotice("Document deleted."); await loadDocuments(); }
    catch (error) { setNotice(error.response?.data?.error || "Could not delete document."); }
    finally { setLoading(false); }
  }

  async function sendMessage(event) {
    event.preventDefault();
    const question = message.trim();
    if (!question || loading) return;
    setMessages(old => [...old, { role: "user", text: question }]);
    setMessage("");
    setLoading(true);
    try {
      const response = await axios.post(`${API}/chat/`, { message: question });
      setMessages(old => [...old, { role: "assistant", text: response.data.reply, sources: response.data.sources || [] }]);
    } catch (error) {
      setMessages(old => [...old, { role: "assistant", text: error.response?.data?.error || "Could not connect to Django. Is the backend running?" }]);
    } finally { setLoading(false); }
  }

  return (
    <main className="page">
      <section className="app-shell">
        <header className="header">
          <div className="logo">RAG</div>
          <div><h1>Document AI Chatbot</h1><p>React · Django · Gemini · FAISS</p></div>
          <span className="status">● RAG enabled</span>
        </header>
        <div className="layout">
          <aside className="documents panel">
            <h2>Knowledge base</h2>
            <p className="muted">Upload PDF, TXT, or Markdown files (max 10 MB).</p>
            <form className="upload-form" onSubmit={uploadDocument}>
              <input type="file" accept=".pdf,.txt,.md" onChange={e => setFile(e.target.files?.[0] || null)} />
              <button type="submit" disabled={loading}>{loading ? "Please wait…" : "Upload and index"}</button>
            </form>
            {notice && <div className="notice">{notice}</div>}
            <h3>Indexed documents ({documents.length})</h3>
            {documents.length === 0 ? <p className="muted empty">No documents uploaded yet.</p> : documents.map(doc => (
              <div className="doc-row" key={doc.document_id}>
                <div className="doc-icon">DOC</div>
                <div className="doc-info"><strong title={doc.filename}>{doc.filename}</strong><small>{doc.chunk_count} chunks</small></div>
                <button className="delete" title="Delete document" onClick={() => deleteDocument(doc.document_id)} disabled={loading}>×</button>
              </div>
            ))}
            <div className="tip"><strong>How RAG works</strong><p>Text is split into chunks, converted to embeddings, stored in FAISS, and searched before Gemini answers.</p></div>
          </aside>

          <section className="chat panel">
            <div className="chat-title"><div><h2>Chat with your documents</h2><p className="muted">Retrieved source passages are attached to answers.</p></div>
              <button className="secondary" onClick={() => setMessages([{ role: "assistant", text: "Chat cleared. Ask a question about your indexed documents." }])}>Clear chat</button>
            </div>
            <div className="chat-box" aria-live="polite">
              {messages.map((item, index) => <article key={`${index}-${item.role}`} className={`message ${item.role}`}>
                <strong>{item.role === "user" ? "You" : "AI assistant"}</strong><p>{item.text}</p>
                {item.sources?.length > 0 && <details className="sources"><summary>Sources used ({item.sources.length})</summary>
                  {item.sources.map((source, i) => <div className="source" key={`${source.filename}-${source.chunk_number}-${i}`}>
                    <strong>{source.filename} · chunk {source.chunk_number}</strong><small>Similarity score: {source.score}</small><p>{source.text}</p>
                  </div>)}
                </details>}
              </article>)}
              {loading && <div className="thinking">Processing…</div>}
            </div>
            <form className="chat-form" onSubmit={sendMessage}>
              <input aria-label="Your message" value={message} onChange={e => setMessage(e.target.value)} placeholder="Ask about your uploaded documents…" disabled={loading} />
              <button type="submit" disabled={loading || !message.trim()}>{loading ? "Wait…" : "Send ↑"}</button>
            </form>
            <p className="footnote">Learning demo · Verify important answers against the source document.</p>
          </section>
        </div>
      </section>
    </main>
  );
}
