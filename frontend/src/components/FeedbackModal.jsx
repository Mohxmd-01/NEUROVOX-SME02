import { CheckCircle, X, DollarSign, MessageSquare } from "lucide-react";
import { useState } from "react";
import { api } from "../services/api";

const OPTS = [
  { id:"won",     label:"Deal Won",       color:"var(--em-lt)",  bg:"var(--em-dim)",   border:"var(--em-br)",   icon:<CheckCircle size={20}/> },
  { id:"lost",    label:"Deal Lost",      color:"var(--rose)",   bg:"var(--rose-dim)", border:"var(--rose-br)", icon:<X size={20}/> },
  { id:"pending", label:"Still Pending",  color:"var(--cyan)",   bg:"var(--cyan-dim)", border:"var(--cyan-br)", icon:<DollarSign size={20}/> },
];

export default function FeedbackModal({ quoteId, quotePrice, onClose, onSubmitted }) {
  const [sel,     setSel]     = useState(null);
  const [price,   setPrice]   = useState("");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [done,    setDone]    = useState(false);

  const submit = async () => {
    if (!sel) return;
    setLoading(true);
    try {
      await api.submitFeedback(quoteId, sel, price ? parseFloat(price) : null, comment);
      setDone(true);
      setTimeout(() => { onSubmitted?.(sel); onClose?.(); }, 1400);
    } catch { } finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <h3>Record Deal Outcome</h3>
            <p>Quote #{quoteId} · Quoted at ₹{quotePrice?.toLocaleString()}/unit</p>
          </div>
          <button className="btn btn-ghost btn-sm" style={{ padding:6 }} onClick={onClose}><X size={15}/></button>
        </div>

        {done ? (
          <div style={{ padding:"36px 24px", textAlign:"center" }}>
            <CheckCircle size={36} style={{ color:"var(--em-lt)", margin:"0 auto 10px", display:"block" }}/>
            <div style={{ fontWeight:700, fontSize:"1rem", color:"var(--t1)" }}>Outcome recorded!</div>
            <div style={{ fontSize:".83rem", color:"var(--t3)", marginTop:5 }}>Decision memory updated for future learning.</div>
          </div>
        ) : (
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">What was the outcome?</label>
              <div className="outcome-row">
                {OPTS.map(o => (
                  <button key={o.id} className={`outcome-btn ${sel===o.id ? `sel-${o.id}` : ""}`}
                    onClick={() => setSel(o.id)}
                    style={{ borderColor: sel===o.id ? o.border : "var(--br-md)", color: sel===o.id ? o.color : "var(--t3)" }}>
                    <span style={{ color: sel===o.id ? o.color : "var(--t3)" }}>{o.icon}</span>
                    <span>{o.label}</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="form-group">
              <label className="form-label"><DollarSign size={11} style={{ verticalAlign:"middle", marginRight:4 }}/>Final Agreed Price (optional)</label>
              <input className="input" type="number" placeholder={`e.g. ${quotePrice || 1000}`} value={price} onChange={e => setPrice(e.target.value)}/>
              <div className="form-hint">Enter the final unit price if it differed from our recommendation.</div>
            </div>
            <div className="form-group">
              <label className="form-label"><MessageSquare size={11} style={{ verticalAlign:"middle", marginRight:4 }}/>Notes (optional)</label>
              <textarea className="textarea" rows={3} style={{ minHeight:72 }}
                placeholder="e.g. Client negotiated on warranty terms…" value={comment} onChange={e => setComment(e.target.value)}/>
            </div>
            <div style={{ display:"flex", gap:9, justifyContent:"flex-end" }}>
              <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
              <button className="btn btn-primary" onClick={submit} disabled={!sel || loading}>
                {loading ? <><div className="spinner" style={{ width:14,height:14,borderWidth:2 }}/> Saving…</> : "Record Outcome"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
