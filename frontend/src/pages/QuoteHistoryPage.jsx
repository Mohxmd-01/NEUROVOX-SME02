import { useState, useEffect } from "react";
import {
  History, Download, Eye, FileText,
  Clock, CheckCircle, ChevronDown, ChevronUp,
  ThumbsUp, XCircle, Target, Calendar,
} from "lucide-react";
import { api } from "../services/api";
import FeedbackModal from "../components/FeedbackModal";

const STRAT_BADGE = {
  aggressive:"badge-rose", "value-based":"badge-indigo",
  premium:"badge-amber", balanced:"badge-indigo", competitive:"badge-cyan",
};

const COUNTRY_FLAGS = {
  India:"🇮🇳", USA:"🇺🇸", UK:"🇬🇧", UAE:"🇦🇪", Germany:"🇩🇪",
  France:"🇫🇷", Singapore:"🇸🇬", Japan:"🇯🇵", Canada:"🇨🇦",
  Australia:"🇦🇺", China:"🇨🇳", Brazil:"🇧🇷", Mexico:"🇲🇽",
  "South Africa":"🇿🇦", Netherlands:"🇳🇱", Italy:"🇮🇹",
};

function formatDateTime(rawDate) {
  if (!rawDate) return { date: "—", time: "—" };
  try {
    // rawDate is "YYYY-MM-DD HH:MM:SS" from backend
    const d = new Date(rawDate.replace(" ", "T"));
    const date = d.toLocaleDateString("en-IN", { day:"2-digit", month:"short", year:"numeric" });
    const time = d.toLocaleTimeString("en-IN", { hour:"2-digit", minute:"2-digit", hour12:true });
    return { date, time };
  } catch {
    return { date: rawDate, time: "" };
  }
}

function OutcomeBadge({ outcome, status }) {
  if (outcome === "won")  return <span className="badge badge-won"><CheckCircle size={9}/> Won</span>;
  if (outcome === "lost") return <span className="badge badge-lost"><XCircle size={9}/> Lost</span>;
  if (outcome === "pending") return <span className="badge badge-pending"><Clock size={9}/> Pending</span>;
  if (status === "finalized") return <span className="badge badge-green"><CheckCircle size={9}/> Finalized</span>;
  return <span className="badge badge-draft"><Clock size={9}/> {status || "draft"}</span>;
}

export default function QuoteHistoryPage() {
  const [quotes, setQuotes]       = useState([]);
  const [expanded, setExpanded]   = useState(null);
  const [expData, setExpData]     = useState(null);
  const [loading, setLoading]     = useState(true);
  const [fbQuote, setFbQuote]     = useState(null);
  const [dlLoading, setDlLoading] = useState({});  // per-quote download loading

  useEffect(() => { load(); }, []);

  const load = async () => {
    try { setQuotes(await api.getQuotes()); }
    catch { }
    finally { setLoading(false); }
  };

  const toggle = async (id) => {
    if (expanded === id) { setExpanded(null); setExpData(null); return; }
    setExpanded(id);
    try { setExpData(await api.getQuote(id)); } catch { setExpData(null); }
  };

  const handleDownload = async (q, e) => {
    e.stopPropagation();
    setDlLoading(prev => ({ ...prev, [q.id]: true }));
    try {
      await api.generateAndDownloadPDF(q.id);
      load(); // refresh list
    } catch (err) {
      console.error("PDF download error:", err);
      alert("PDF download failed: " + (err.message || "Unknown error"));
    } finally {
      setDlLoading(prev => ({ ...prev, [q.id]: false }));
    }
  };

  return (
    <>
      <div className="page-header page-header-row">
        <div>
          <h1>Quote History</h1>
          <p>Track and download all generated quotations</p>
        </div>
        <div style={{ display:"flex", gap:8 }}>
          <span className="badge badge-green" style={{ padding:"5px 12px", fontSize:".75rem" }}>{quotes.filter(q=>q.outcome==="won").length} Won</span>
          <span className="badge badge-rose"  style={{ padding:"5px 12px", fontSize:".75rem" }}>{quotes.filter(q=>q.outcome==="lost").length} Lost</span>
          <span className="badge badge-muted" style={{ padding:"5px 12px", fontSize:".75rem" }}>{quotes.length} Total</span>
        </div>
      </div>

      {loading ? (
        <div className="loading-row"><div className="spinner"/><span>Loading quotes…</span></div>
      ) : quotes.length === 0 ? (
        <div className="card"><div className="empty-state">
          <div className="empty-icon"><History size={24}/></div>
          <h3>No quotes yet</h3>
          <p>Process an RFP to generate your first quotation</p>
        </div></div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr>
              <th>Quote ID</th>
              <th>Client</th>
              <th>Product</th>
              <th>Qty</th>
              <th>Unit Price</th>
              <th>Total</th>
              <th>Strategy</th>
              <th><Calendar size={12} style={{verticalAlign:"middle",marginRight:3}}/>Date & Time</th>
              <th>Outcome</th>
              <th>Actions</th>
            </tr></thead>
            <tbody>
              {quotes.map(q => {
                const { date, time } = formatDateTime(q.date);
                const isExpanded = expanded === q.id;
                const isDlLoading = dlLoading[q.id];
                return (
                  <>
                    <tr key={q.id} onClick={() => toggle(q.id)} style={{cursor:"pointer"}}>
                      <td>
                        <span className="td-brand td-mono">IQ-{q.id}</span>
                      </td>
                      <td className="td-primary">{q.client}</td>
                      <td style={{ color:"var(--t2)", fontSize:".83rem" }}>{q.product}</td>
                      <td>{q.quantity?.toLocaleString()}</td>
                      <td className="td-mono" style={{ fontWeight:600 }}>₹{q.price?.toLocaleString()}</td>
                      <td className="td-green td-mono">₹{q.total?.toLocaleString()}</td>
                      <td><span className={`badge ${STRAT_BADGE[q.strategy]||"badge-muted"}`}>{q.strategy}</span></td>
                      <td>
                        <div style={{ fontSize:".83rem", fontWeight:600, color:"var(--t1)" }}>{date}</div>
                        <div style={{ fontSize:".72rem", color:"var(--t3)", marginTop:2 }}>{time}</div>
                      </td>
                      <td><OutcomeBadge outcome={q.outcome} status={q.status}/></td>
                      <td onClick={e => e.stopPropagation()}>
                        <div style={{ display:"flex", gap:5, alignItems:"center" }}>
                          {/* Expand / collapse */}
                          <button className="btn btn-ghost btn-sm" onClick={() => toggle(q.id)} title={isExpanded?"Collapse":"View Details"}>
                            {isExpanded ? <ChevronUp size={14}/> : <Eye size={14}/>}
                          </button>

                          {/* Download PDF — clear label */}
                          <button
                            className={`btn btn-sm ${q.has_pdf ? "btn-em" : "btn-outline"}`}
                            onClick={(e) => handleDownload(q, e)}
                            disabled={isDlLoading}
                            title={q.has_pdf ? "Download PDF" : "Generate & Download PDF"}
                            style={{ gap:5, fontSize:".73rem", padding:"4px 10px", whiteSpace:"nowrap" }}
                          >
                            {isDlLoading ? (
                              <><div className="spinner" style={{width:11,height:11,borderWidth:2}}/> Saving…</>
                            ) : q.has_pdf ? (
                              <><Download size={12}/> PDF</>
                            ) : (
                              <><FileText size={12}/> Get PDF</>
                            )}
                          </button>

                          {/* Outcome feedback */}
                          <button className="btn btn-ghost btn-sm"
                            style={{ color: q.outcome ? "var(--em-lt)" : "var(--t3)" }}
                            onClick={() => setFbQuote({ id:q.id, price:q.price })}
                            title="Record outcome">
                            <ThumbsUp size={13}/>
                          </button>
                        </div>
                      </td>
                    </tr>
                    {isExpanded && expData && (
                      <tr key={`${q.id}-exp`}>
                        <td colSpan="10" style={{ padding:"18px 24px", background:"rgba(99,102,241,.04)", borderBottom:"1px solid var(--br)" }}>
                          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:20 }}>
                            <div>
                              <div style={{ fontSize:".72rem", fontWeight:700, color:"var(--t3)", textTransform:"uppercase", letterSpacing:".05em", marginBottom:8 }}>AI Reasoning</div>
                              <p style={{ fontSize:".83rem", lineHeight:1.65, color:"var(--t2)" }}>{expData.strategy?.reasoning?.substring(0,280)}…</p>
                              <div style={{ display:"flex", gap:7, flexWrap:"wrap", marginTop:8 }}>
                                <span className="badge badge-green">Win: {expData.strategy?.win_probability}</span>
                                <span className="badge badge-indigo">Margin: {expData.strategy?.margin_percent}%</span>
                              </div>
                            </div>
                            <div>
                              <div style={{ fontSize:".72rem", fontWeight:700, color:"var(--t3)", textTransform:"uppercase", letterSpacing:".05em", marginBottom:8 }}>Market Data</div>
                              {[
                                { l:"Competitor", v:expData.competitor?.competitor_name },
                                { l:"Their Price", v:`₹${expData.competitor?.competitor_price}` },
                                { l:"Market Avg",  v:`₹${expData.competitor?.market_avg}` },
                              ].map(row => (
                                <div key={row.l} className="result-row">
                                  <span className="rl">{row.l}</span>
                                  <span className="rv">{row.v}</span>
                                </div>
                              ))}
                            </div>
                            <div>
                              <div style={{ fontSize:".72rem", fontWeight:700, color:"var(--t3)", textTransform:"uppercase", letterSpacing:".05em", marginBottom:8 }}>Value & Tactics</div>
                              {expData.strategy?.value_additions?.slice(0,3).map((va,i) => (
                                <div key={i} style={{ display:"flex", gap:6, fontSize:".8rem", color:"var(--t2)", marginBottom:5 }}>
                                  <CheckCircle size={11} style={{ color:"var(--em-lt)", flexShrink:0, marginTop:2 }}/>{va}
                                </div>
                              ))}
                              {expData.strategy?.negotiation_tactics?.slice(0,2).map((t,i) => (
                                <div key={i} style={{ fontSize:".77rem", color:"var(--t3)", marginBottom:4, paddingLeft:8, borderLeft:"2px solid var(--am-br)" }}>{t}</div>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {fbQuote && (
        <FeedbackModal
          quoteId={fbQuote.id} quotePrice={fbQuote.price}
          onClose={() => setFbQuote(null)}
          onSubmitted={() => { setFbQuote(null); load(); }}
        />
      )}
    </>
  );
}
