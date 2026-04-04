import { Handshake, ChevronRight, Lightbulb, TrendingDown, AlertTriangle } from "lucide-react";

const COLORS = [
  { color:"var(--cyan)", bg:"var(--cyan-dim)", border:"var(--cyan-br)", icon:Handshake },
  { color:"var(--em-lt)", bg:"var(--em-dim)", border:"var(--em-br)", icon:TrendingDown },
  { color:"var(--am-lt)", bg:"var(--am-dim)", border:"var(--am-br)", icon:Lightbulb },
];

export default function NegotiationPanel({ tactics }) {
  if (!tactics?.length) return null;
  return (
    <div className="card negot-panel mb-md">
      <div className="card-header">
        <span className="card-title"><Handshake size={13} style={{ color:"var(--cyan)" }}/> Negotiation Intelligence</span>
        <span className="badge badge-cyan" style={{ fontSize:".66rem" }}>{tactics.length} tactic{tactics.length>1?"s":""}</span>
      </div>
      <p style={{ fontSize:".79rem", color:"var(--t3)", marginBottom:14, lineHeight:1.55 }}>
        AI negotiation playbook — use these if the client pushes back on pricing.
      </p>
      {tactics.map((t, i) => {
        const c = COLORS[i % COLORS.length];
        const Icon = c.icon;
        return (
          <div key={i} className="negot-item">
            <div className="negot-icon" style={{ background:c.bg, border:`1px solid ${c.border}`, color:c.color }}><Icon size={14}/></div>
            <div style={{ flex:1 }}>
              <div className="negot-num" style={{ color:c.color }}>Tactic {i+1}</div>
              <div className="negot-text">{t}</div>
            </div>
            <ChevronRight size={13} style={{ color:"var(--t3)", flexShrink:0 }}/>
          </div>
        );
      })}
      <div className="negot-warn"><AlertTriangle size={12}/> Internal use only — do not share with clients.</div>
    </div>
  );
}
