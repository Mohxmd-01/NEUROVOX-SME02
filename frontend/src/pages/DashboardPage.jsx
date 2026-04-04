import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText, TrendingUp, DollarSign, Brain,
  Zap, Database, CheckCircle, Clock, Target,
  ArrowRight, BarChart3, Activity, Globe,
} from "lucide-react";
import { api } from "../services/api";

export default function DashboardPage() {
  const nav = useNavigate();
  const [quotes,  setQuotes]  = useState([]);
  const [health,  setHealth]  = useState(null);
  const [fbStats, setFbStats] = useState(null);
  const [kb,      setKb]      = useState(null);

  useEffect(() => {
    api.getQuotes().then(setQuotes).catch(() => {});
    api.health().then(setHealth).catch(() => {});
    api.getFeedbackStats().then(setFbStats).catch(() => {});
    api.knowledgeStatus().then(setKb).catch(() => {});
  }, []);

  const total    = quotes.length;
  const revenue  = quotes.reduce((s, q) => s + (q.total || 0), 0);
  const winRate  = fbStats?.win_rate ?? 0;
  const memory   = health?.memory_cases ?? 0;
  const won      = fbStats?.won ?? 0;
  const lost     = fbStats?.lost ?? 0;
  const pending  = fbStats?.pending ?? 0;
  const fbTotal  = fbStats?.total_feedback ?? 0;

  const kpis = [
    { label:"Quotes Generated", value: total||"—", icon:<FileText size={16}/>,   color:"c-indigo", change: total>0?"↑ This session":"Process first RFP", up:true },
    { label:"Win Rate",         value: fbTotal>0?`${winRate}%`:"—", icon:<TrendingUp size={16}/>, color:"c-em", change: fbTotal>0?`${won}W · ${lost}L · ${pending}P`:"Record outcomes to track", up:true },
    { label:"Revenue Pipeline", value: revenue>0?`₹${(revenue/100000).toFixed(1)}L`:"—", icon:<DollarSign size={16}/>, color:"c-am", change:"↑ Total quoted", up:true },
    { label:"Memory Cases",     value: memory, icon:<Brain size={16}/>, color:"c-rose", change:"Decision memory", up:false },
    { label:"Sourcing Engine",  value: "Online", icon:<Globe size={16}/>, color:"c-cyan", change:"9 supplier regions", up:true },
  ];

  const recentQuotes = quotes.slice(-5).reverse();

  const stratBadge = (s) => {
    const m = { aggressive:"badge-rose", premium:"badge-amber", balanced:"badge-indigo", competitive:"badge-cyan", "value-based":"badge-indigo" };
    return m[s] || "badge-muted";
  };
  const outcomeBadge = (o, status) => {
    if (o === "won")    return <span className="badge badge-won"><CheckCircle size={9}/> Won</span>;
    if (o === "lost")   return <span className="badge badge-lost"><Target size={9}/> Lost</span>;
    if (o === "pending") return <span className="badge badge-pending"><Clock size={9}/> Pending</span>;
    return <span className="badge badge-draft"><Clock size={9}/> {status || "draft"}</span>;
  };

  return (
    <>
      {/* Header */}
      <div className="page-header page-header-row">
        <div>
          <h1>Good morning 👋</h1>
          <p>Here's your IntelliQuote intelligence summary</p>
        </div>
        <button className="btn btn-primary btn-lg" onClick={() => nav("/rfp")}>
          <Zap size={16}/> Process New RFP
        </button>
      </div>

      {/* KPI strip */}
      <div className="kpi-grid">
        {kpis.map((k, i) => (
          <div key={i} className={`kpi-card ${k.color}`} style={{ animationDelay: `${i * 0.06}s` }}>
            <div className="kpi-top">
              <span className="kpi-label">{k.label}</span>
              <div className="kpi-icon">{k.icon}</div>
            </div>
            <div className="kpi-value">{k.value}</div>
            <div className={`kpi-change ${k.up ? "up" : "neutral"}`}>{k.change}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Recent decisions */}
        <div className="card">
          <div className="card-header">
            <span className="card-title"><FileText size={13}/> Recent Decisions</span>
            <button className="btn btn-ghost btn-sm" onClick={() => nav("/quotes")}>
              View All <ArrowRight size={12}/>
            </button>
          </div>
          {recentQuotes.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon"><FileText size={22}/></div>
              <h3>No quotes yet</h3>
              <p>Process your first RFP to get started</p>
              <button className="btn btn-primary" style={{ marginTop:14 }} onClick={() => nav("/rfp")}>
                <Zap size={13}/> Start now
              </button>
            </div>
          ) : (
            <>
              <div className="table-wrap">
                <table className="table">
                  <thead><tr><th>Client</th><th>Total</th><th>Strategy</th><th>Outcome</th></tr></thead>
                  <tbody>
                    {recentQuotes.map(q => (
                      <tr key={q.id} onClick={() => nav("/quotes")}>
                        <td className="td-primary">{q.client}</td>
                        <td className="td-green td-mono">₹{q.total?.toLocaleString()}</td>
                        <td><span className={`badge ${stratBadge(q.strategy)}`}>{q.strategy}</span></td>
                        <td>{outcomeBadge(q.outcome, q.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {fbTotal > 0 && (
                <div style={{ marginTop:14, paddingTop:14, borderTop:"1px solid var(--br)" }}>
                  <div style={{ display:"flex", justifyContent:"space-between", fontSize:".72rem", color:"var(--t3)", marginBottom:6 }}>
                    <span>Deal pipeline</span><span>{fbTotal} tracked</span>
                  </div>
                  <div className="pipe-bar-track">
                    {won     > 0 && <div className="pipe-bar-seg" style={{ width:`${(won/fbTotal)*100}%`,     background:"var(--em-lt)"  }} />}
                    {pending > 0 && <div className="pipe-bar-seg" style={{ width:`${(pending/fbTotal)*100}%`, background:"var(--cyan)"   }} />}
                    {lost    > 0 && <div className="pipe-bar-seg" style={{ width:`${(lost/fbTotal)*100}%`,    background:"var(--rose)"   }} />}
                  </div>
                  <div style={{ display:"flex", gap:12, marginTop:7 }}>
                    {[["Won",won,"var(--em-lt)"],["Pending",pending,"var(--cyan)"],["Lost",lost,"var(--rose)"]].map(([l,c,col])=>(
                      <div key={l} style={{ display:"flex", alignItems:"center", gap:5, fontSize:".71rem" }}>
                        <div style={{ width:7,height:7,borderRadius:"50%",background:col }} />
                        <span style={{ color:"var(--t3)" }}>{l}:</span>
                        <span style={{ fontWeight:700, color:col }}>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Right column */}
        <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
          {/* Quick Actions */}
          <div className="card">
            <div className="card-header">
              <span className="card-title"><Activity size={13}/> Quick Actions</span>
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
              {[
                { icon:<FileText size={15}/>, title:"Process RFP", sub:"Get AI pricing decision in seconds", action:()=>nav("/rfp"), primary:true },
                { icon:<BarChart3 size={15}/>, title:"Quote History", sub:"Review past decisions & outcomes", action:()=>nav("/quotes") },
                { icon:<Database size={15}/>, title:"Knowledge Base", sub:"Query policies & company docs", action:()=>nav("/knowledge") },
              ].map((a, i) => (
                <button key={i} onClick={a.action}
                  className={`btn ${a.primary ? "btn-primary" : "btn-outline"} btn-lg`}
                  style={{ width:"100%", justifyContent:"flex-start", gap:12, textAlign:"left" }}>
                  {a.icon}
                  <div>
                    <div style={{ fontWeight:700 }}>{a.title}</div>
                    <div style={{ fontSize:".72rem", opacity:.65, fontWeight:400, marginTop:1 }}>{a.sub}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* System status */}
          <div className="card">
            <div className="card-header">
              <span className="card-title"><Activity size={13}/> System Status</span>
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:7 }}>
              {[
                { label:"AI Engine",       ok:!!health,   detail:`v${health?.version||"3.0"}` },
                { label:"Sourcing Engine", ok:!!health?.sourcing_engine, detail:health?.sourcing_engine||"online" },
                { label:"Knowledge Index", ok:!!kb,       detail:`${kb?.total_chunks||0} chunks` },
                { label:"Decision Memory", ok:true,       detail:`${memory} cases` },
                { label:"Feedback System", ok:true,       detail:`${fbTotal} tracked` },
              ].map(item => (
                <div key={item.label} style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"8px 12px", background:"var(--surface-2)", borderRadius:"var(--r-md)", border:"1px solid var(--br)" }}>
                  <div style={{ display:"flex", alignItems:"center", gap:9 }}>
                    <span style={{ width:6,height:6,borderRadius:"50%", background:item.ok?"var(--em-lt)":"var(--rose)", boxShadow:item.ok?"0 0 6px var(--em)":"none", display:"inline-block" }} />
                    <span style={{ fontSize:".82rem", color:"var(--t2)", fontWeight:500 }}>{item.label}</span>
                  </div>
                  <div style={{ textAlign:"right" }}>
                    <span className={`badge ${item.ok?"badge-green":"badge-rose"}`}>{item.ok?"Online":"Offline"}</span>
                    <div style={{ fontSize:".67rem", color:"var(--t3)", marginTop:2 }}>{item.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop:16 }}>
        <div className="card-header">
          <span className="card-title"><BarChart3 size={13}/> How IntelliQuote Works</span>
        </div>
        <div style={{ display:"flex" }}>
          {[
            { n:"01", icon:<FileText size={16}/>,   title:"Parse RFP",           desc:"LLM extracts product, qty, geo & budget" },
            { n:"02", icon:<Database size={16}/>,   title:"Knowledge Retrieval",  desc:"RAG + decision memory recall" },
            { n:"03", icon:<TrendingUp size={16}/>, title:"Price & Compete",      desc:"Cost structure vs market landscape" },
            { n:"04", icon:<Globe size={16}/>,      title:"Sourcing Analysis",    desc:"Local · Offshore · Near-Client scoring" },
            { n:"05", icon:<Brain size={16}/>,      title:"Unified AI Decision",  desc:"LLM with full context generates strategy" },
            { n:"06", icon:<CheckCircle size={16}/>,title:"Output + PDF",         desc:"Decision, tactics & professional PDF" },
          ].map((s, i, arr) => (
            <div key={s.n} style={{ flex:1, padding:"14px 10px", textAlign:"center", position:"relative" }}>
              {i < arr.length-1 && <div style={{ position:"absolute", top:28, right:"-1px", width:1, height:20, background:"var(--br)" }} />}
              <div style={{ width:40,height:40,borderRadius:"50%", background:"linear-gradient(135deg,var(--brand),var(--brand-h))", display:"flex", alignItems:"center", justifyContent:"center", margin:"0 auto 9px", color:"white", boxShadow:"var(--sh-brand)" }}>
                {s.icon}
              </div>
              <div style={{ fontSize:".62rem", fontWeight:800, color:"var(--brand-lt)", letterSpacing:".1em", marginBottom:3 }}>STEP {s.n}</div>
              <div style={{ fontFamily:"var(--heading)", fontSize:".8rem", fontWeight:700, color:"var(--t1)", marginBottom:3 }}>{s.title}</div>
              <div style={{ fontSize:".73rem", color:"var(--t3)", lineHeight:1.45 }}>{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
