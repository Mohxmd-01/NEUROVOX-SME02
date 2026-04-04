import { useState, useEffect, useRef } from "react";
import {
  Upload, FileText, BookOpen, Send, AlertTriangle,
  Database, File, Table as TableIcon, Mail, Sparkles,
} from "lucide-react";
import { api } from "../services/api";

export default function KnowledgeBasePage() {
  const [kbStatus,      setKbStatus]      = useState(null);
  const [uploading,     setUploading]     = useState(false);
  const [uploadMsg,     setUploadMsg]     = useState(null);
  const [chatMessages,  setChatMessages]  = useState([]);
  const [chatInput,     setChatInput]     = useState("");
  const [chatLoading,   setChatLoading]   = useState(false);
  const [dragOver,      setDragOver]      = useState(false);
  const fileInputRef = useRef(null);
  const chatEndRef   = useRef(null);

  useEffect(() => { loadStatus(); }, []);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior:"smooth" }); }, [chatMessages]);

  const loadStatus = async () => {
    try { setKbStatus(await api.knowledgeStatus()); } catch {}
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    setUploading(true); setUploadMsg(null);
    try {
      const r = await api.uploadDocument(file);
      setUploadMsg({ type:"success", text: r.message });
      await loadStatus();
    } catch (err) {
      setUploadMsg({ type:"error", text: err.message });
    } finally { setUploading(false); }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;
    const query = chatInput.trim();
    setChatInput("");
    setChatMessages(p => [...p, { role:"user", content:query }]);
    setChatLoading(true);
    try {
      const r = await api.knowledgeChat(query);
      setChatMessages(p => [...p, { role:"assistant", content:r.answer, sources:r.sources, conflicts:r.conflicts }]);
    } catch (err) {
      setChatMessages(p => [...p, { role:"assistant", content:`Error: ${err.message}` }]);
    } finally { setChatLoading(false); }
  };

  const getDocIcon = (src) => {
    if (src?.endsWith(".pdf"))  return { icon:File,      cls:"pdf" };
    if (src?.match(/\.xlsx?/))  return { icon:TableIcon, cls:"excel" };
    if (src?.endsWith(".json")) return { icon:Mail,      cls:"email" };
    return { icon:FileText, cls:"pdf" };
  };

  const SUGGESTED = [
    "What is our minimum pricing margin?",
    "What discount can we offer for bulk orders?",
    "What are our delivery terms?",
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Knowledge Base</h1>
        <p>Upload documents, query company knowledge, and ask the AI anything</p>
      </div>

      {/* Stats */}
      <div className="stats-grid" style={{ gridTemplateColumns:"repeat(3,1fr)" }}>
        <div className="stat-card blue">
          <div className="stat-card-top">
            <span className="stat-card-label">Knowledge Chunks</span>
            <div className="stat-card-icon"><Database size={17} /></div>
          </div>
          <div className="stat-card-value">{kbStatus?.total_chunks || 0}</div>
          <div className="stat-card-change up">↑ Indexed</div>
        </div>
        <div className="stat-card green">
          <div className="stat-card-top">
            <span className="stat-card-label">Source Documents</span>
            <div className="stat-card-icon"><FileText size={17} /></div>
          </div>
          <div className="stat-card-value">{kbStatus?.sources?.length || 0}</div>
          <div className="stat-card-change up">↑ Active</div>
        </div>
        <div className="stat-card purple">
          <div className="stat-card-top">
            <span className="stat-card-label">Index Status</span>
            <div className="stat-card-icon"><BookOpen size={17} /></div>
          </div>
          <div className="stat-card-value" style={{ fontSize:"1.2rem" }}>
            {kbStatus?.index_loaded ? "Active" : "Offline"}
          </div>
          <div className={`stat-card-change ${kbStatus?.index_loaded ? "up" : "down"}`}>
            {kbStatus?.index_loaded ? "↑ Ready to search" : "↓ Not loaded"}
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Left: Upload + Docs */}
        <div style={{ display:"flex", flexDirection:"column", gap:"16px" }}>
          {/* Upload */}
          <div
            className={`upload-zone ${dragOver ? "drag-over" : ""}`}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => { e.preventDefault(); setDragOver(false); handleFileUpload(e.dataTransfer.files?.[0]); }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file" ref={fileInputRef}
              onChange={e => handleFileUpload(e.target.files?.[0])}
              accept=".pdf,.xlsx,.xls,.json,.txt"
              style={{ display:"none" }}
            />
            <div className="upload-zone-icon">
              {uploading ? <span className="loading-spinner" /> : <Upload size={26} />}
            </div>
            <h3>{uploading ? "Uploading & Indexing…" : "Upload Document"}</h3>
            <p>Drag & drop or click — PDF, Excel, JSON, Text</p>
          </div>

          {uploadMsg && (
            <div className="conflict-alert" style={{
              background: uploadMsg.type === "success" ? "rgba(16,185,129,.08)" : "rgba(239,68,68,.08)",
              borderColor: uploadMsg.type === "success" ? "rgba(16,185,129,.3)" : "rgba(239,68,68,.3)",
            }}>
              <div className="conflict-alert-text" style={{ color: uploadMsg.type === "success" ? "var(--g400)" : "var(--red400)" }}>
                {uploadMsg.text}
              </div>
            </div>
          )}

          {/* Document list */}
          <div className="card">
            <div className="card-header">
              <span className="card-title"><FileText size={13} /> Indexed Documents</span>
              {kbStatus?.sources?.length > 0 && (
                <span className="badge badge-green">{kbStatus.sources.length} active</span>
              )}
            </div>
            {kbStatus?.sources?.length > 0 ? (
              <div className="doc-list">
                {kbStatus.sources.map((src, i) => {
                  const { icon:DocIcon, cls } = getDocIcon(src);
                  return (
                    <div key={i} className="doc-item">
                      <div className={`doc-icon ${cls}`}><DocIcon size={16} /></div>
                      <div className="doc-info">
                        <div className="doc-name">{src}</div>
                        <div className="doc-meta">Indexed & searchable</div>
                      </div>
                      <span className="badge badge-green">Active</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state" style={{ padding:"24px" }}>
                <div className="empty-state-icon"><Database size={20} /></div>
                <p>No documents indexed. Upload to get started!</p>
              </div>
            )}
          </div>
        </div>

        {/* Right: Chat */}
        <div className="chat-container" style={{ minHeight:"520px" }}>
          <div style={{ padding:"16px 20px", borderBottom:"1px solid var(--border)", background:"rgba(139,92,246,0.06)" }}>
            <h3 style={{ fontSize:".88rem", fontWeight:700, color:"var(--txt-primary)", display:"flex", alignItems:"center", gap:"8px" }}>
              <Sparkles size={15} style={{ color:"var(--v400)" }} /> Ask the Knowledge Base
            </h3>
            <p style={{ fontSize:".78rem", color:"var(--txt-muted)", marginTop:"3px" }}>
              Ask questions about pricing, policies, and past deals
            </p>
          </div>

          <div className="chat-messages">
            {chatMessages.length === 0 && (
              <div>
                <div className="empty-state" style={{ padding:"30px", marginBottom:"16px" }}>
                  <div className="empty-state-icon"><BookOpen size={22} /></div>
                  <h3>Start a conversation</h3>
                  <p>Ask about policies, pricing rules, or client history</p>
                </div>
                {/* Suggested questions */}
                <div style={{ padding:"0 4px", display:"flex", flexDirection:"column", gap:"8px" }}>
                  {SUGGESTED.map((q, i) => (
                    <button key={i}
                      onClick={() => setChatInput(q)}
                      style={{
                        padding:"10px 14px", background:"rgba(139,92,246,.07)",
                        border:"1px solid var(--border-v)", borderRadius:"var(--r-md)",
                        color:"var(--v300)", fontSize:".82rem", cursor:"pointer",
                        textAlign:"left", transition:"all var(--fast) var(--ease)",
                        fontFamily:"var(--font)", fontWeight:500,
                      }}
                      onMouseOver={e => e.currentTarget.style.background = "rgba(139,92,246,.14)"}
                      onMouseOut={e  => e.currentTarget.style.background = "rgba(139,92,246,.07)"}
                    >
                      💬 {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {chatMessages.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role}`}>
                <div className="chat-avatar">{msg.role === "user" ? "You" : "AI"}</div>
                <div>
                  <div className="chat-bubble">{msg.content}</div>
                  {msg.sources?.length > 0 && (
                    <div style={{ marginTop:"6px", display:"flex", flexWrap:"wrap", gap:"4px" }}>
                      {msg.sources.map((s, j) => (
                        <span key={j} className="source-tag">
                          📄 {s.source} ({(s.score * 100).toFixed(0)}%)
                        </span>
                      ))}
                    </div>
                  )}
                  {msg.conflicts && Object.keys(msg.conflicts).length > 0 && (
                    <div className="conflict-alert" style={{ marginTop:"8px" }}>
                      <AlertTriangle size={13} className="conflict-alert-icon" />
                      <div className="conflict-alert-text">
                        <strong>Data conflict detected</strong> — most authoritative source was used.
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {chatLoading && (
              <div className="chat-message assistant">
                <div className="chat-avatar">AI</div>
                <div className="chat-bubble" style={{ display:"flex", alignItems:"center", gap:"10px" }}>
                  <span className="loading-spinner" style={{ width:14, height:14, borderWidth:"1.5px" }} />
                  Searching knowledge base…
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <form className="chat-input-bar" onSubmit={handleChatSubmit}>
            <input
              type="text"
              placeholder="Ask about pricing, policies, client history…"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              disabled={chatLoading}
            />
            <button type="submit" className="btn btn-primary" disabled={chatLoading || !chatInput.trim()}>
              <Send size={15} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
