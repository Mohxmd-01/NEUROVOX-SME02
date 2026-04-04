import { Star, CheckCircle, Globe } from "lucide-react";

const META = {
  aggressive: { label:"Aggressive", color:"var(--rose)",       bg:"var(--rose-dim)",  border:"var(--rose-br)",  topBar:"linear-gradient(90deg,var(--rose),#fb7185)" },
  balanced:   { label:"Balanced",   color:"var(--brand-lt)",   bg:"var(--brand-dim)", border:"var(--brand-br)", topBar:"linear-gradient(90deg,var(--brand),var(--brand-lt))" },
  premium:    { label:"Premium",    color:"var(--am-lt)",      bg:"var(--am-dim)",    border:"var(--am-br)",    topBar:"linear-gradient(90deg,var(--am),var(--am-lt))" },
};

function Bar({ value, max, color }) {
  const pct = Math.min(Math.round((value / max) * 100), 100);
  return (
    <div className="mini-bar">
      <div className="mini-bar-fill" style={{ width:`${pct}%`, background:color, boxShadow:`0 0 6px ${color}80` }} />
    </div>
  );
}

export default function StrategyComparisonTable({ strategies, recommended, geo, currencyRate }) {
  // geo: { currency, currency_symbol, is_international }
  // currencyRate: { rate, symbol, currency } from result.currency or result.unit_currency
  const isIntl = geo?.is_international;
  const localSym = currencyRate?.symbol || geo?.currency_symbol || "₹";
  const rate = currencyRate?.rate || 1;
  const formatLocal = (inrPrice) => {
    if (!inrPrice) return "—";
    if (!isIntl) return `₹${inrPrice?.toLocaleString()}`;
    const converted = (inrPrice / rate).toFixed(0);
    return `${localSym}${Number(converted).toLocaleString()}`;
  };
  if (!strategies) return null;
  const modes = ["aggressive","balanced","premium"];
  const maxPrice = Math.max(...modes.map(m => strategies[m]?.final_price || 0));

  return (
    <div className="mb-md">
      <div className="strat-grid">
        {modes.map(mode => {
          const s = strategies[mode];
          if (!s) return null;
          const m = META[mode];
          const isRec = mode === recommended;
          return (
            <div key={mode} className={`strat-card ${isRec ? "recommended" : ""}`}
              style={{ background: isRec ? m.bg : "var(--surface-1)", border:`1px solid ${isRec ? m.border : "var(--br)"}`, boxShadow: isRec ? `0 8px 28px ${m.color}25, var(--sh-md)` : "none" }}>
              <div className="strat-top-bar" style={{ background: m.topBar }} />
              <div className="strat-head">
                <span className="strat-name" style={{ color: m.color }}>{m.label}</span>
                {isRec && <span className="badge badge-green" style={{ fontSize:".64rem" }}><Star size={8}/> AI Pick</span>}
              </div>
              <div className="strat-price" style={{ color: m.color }}>
                {isIntl ? formatLocal(s.final_price) : `₹${s.final_price?.toLocaleString()}`}
              </div>
              {isIntl && (
                <div style={{ fontSize:".72rem", color:"var(--t3)", marginTop:-4, marginBottom:4 }}>
                  ₹{s.final_price?.toLocaleString()} INR
                </div>
              )}
              <Bar value={s.final_price} max={maxPrice} color={m.color} />
              <div className="strat-mini-stat" style={{ marginTop:12 }}>
                <div className="strat-mini-item">
                  <div className="strat-mini-item-label">Win %</div>
                  <div className="strat-mini-item-val" style={{ color:"var(--em-lt)" }}>{s.win_probability_pct}%</div>
                  <Bar value={s.win_probability_pct} max={100} color="var(--em-lt)" />
                </div>
                <div className="strat-mini-item">
                  <div className="strat-mini-item-label">Margin</div>
                  <div className="strat-mini-item-val" style={{ color:"var(--cyan)" }}>{s.margin_percent}%</div>
                  <Bar value={s.margin_percent} max={40} color="var(--cyan)" />
                </div>
              </div>
              <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", fontSize:".77rem" }}>
                <span style={{ color:"var(--t3)" }}>Risk</span>
                <span className={`badge ${s.risk_level==="low"?"badge-green":s.risk_level==="high"?"badge-rose":"badge-amber"}`}>{s.risk_level}</span>
              </div>
              {s.value_additions?.length > 0 && (
                <div style={{ marginTop:10, paddingTop:10, borderTop:"1px solid var(--br)" }}>
                  {s.value_additions.slice(0,2).map((va,i) => (
                    <div key={i} style={{ display:"flex", gap:6, fontSize:".74rem", color:"var(--t2)", marginBottom:3 }}>
                      <CheckCircle size={10} style={{ color:"var(--em-lt)", flexShrink:0, marginTop:2 }} />{va}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {strategies[recommended]?.reasoning && (
        <div style={{ padding:"12px 16px", background:"var(--brand-dim)", border:"1px solid var(--brand-br)", borderRadius:"var(--r-md)", fontSize:".83rem", color:"var(--t2)", lineHeight:1.65 }}>
          <span style={{ fontWeight:700, color:"var(--brand-lt)" }}>AI Pick Rationale: </span>
          {strategies[recommended].reasoning}
          {isIntl && (
            <div style={{ marginTop:8, fontSize:".75rem", color:"var(--t3)", display:"flex", alignItems:"center", gap:5 }}>
              <Globe size={11}/> Note: All base prices shown in INR (TechFlow internal). Final client invoice in {geo?.currency}.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
