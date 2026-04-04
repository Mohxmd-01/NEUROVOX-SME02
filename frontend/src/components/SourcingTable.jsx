import { Globe, TrendingDown, Clock, Award, CheckCircle, Star } from "lucide-react";

const COUNTRY_FLAGS = {
  India: "🇮🇳", China: "🇨🇳", Vietnam: "🇻🇳", Germany: "🇩🇪",
  USA: "🇺🇸", UAE: "🇦🇪", Singapore: "🇸🇬", Bangladesh: "🇧🇩", Mexico: "🇲🇽",
};

const TYPE_COLORS = {
  local:       { bar: "#10b981", text: "#166534", bg: "#f0fdf4", border: "#bbf7d0" },
  export:      { bar: "#f59e0b", text: "#9a3412", bg: "#fff7ed", border: "#fed7aa" },
  near_client: { bar: "#0284c7", text: "#1d4ed8", bg: "#eff6ff", border: "#bfdbfe" },
};

function ScoreBar({ score, color }) {
  return (
    <div className="score-bar-wrap">
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="score-val" style={{ color }}>{score.toFixed(0)}</span>
    </div>
  );
}

function QualityDots({ score }) {
  const filled = Math.round(score * 5);
  return (
    <div style={{ display: "flex", gap: 3 }}>
      {[1,2,3,4,5].map(i => (
        <div key={i} style={{
          width: 8, height: 8, borderRadius: "50%",
          background: i <= filled ? "#0284c7" : "#dce8f4",
          transition: "background .3s",
        }} />
      ))}
    </div>
  );
}

export default function SourcingTable({ sourcing }) {
  if (!sourcing) return null;

  const { recommended, alternatives, sourcing_reasoning, cost_impact_percent, savings_per_unit, strategy_note } = sourcing;
  const allOptions = [recommended, ...alternatives];

  const savingsPositive = savings_per_unit > 0;
  const impactColor = savingsPositive ? "var(--em)" : "var(--rose)";

  return (
    <div>
      {/* Top metrics strip */}
      <div className="sourcing-banner">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 12,
            background: "linear-gradient(135deg,#0284c7,#0ea5e9)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 14px rgba(2,132,199,.28)",
          }}>
            <Globe size={20} color="white" />
          </div>
          <div>
            <div style={{ fontFamily: "var(--heading)", fontWeight: 800, fontSize: "1rem", color: "var(--t1)" }}>
              {recommended.region_label}
            </div>
            <div style={{ fontSize: ".75rem", color: "var(--t3)", marginTop: 2 }}>
              Recommended Sourcing · Score {recommended.weighted_score.toFixed(0)}/100
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
          {[
            {
              label: "Cost Impact",
              value: savingsPositive ? `−${Math.abs(cost_impact_percent).toFixed(1)}%` : `+${Math.abs(cost_impact_percent).toFixed(1)}%`,
              color: impactColor,
              icon: <TrendingDown size={13} />,
            },
            {
              label: "Savings/Unit",
              value: savingsPositive ? `₹${savings_per_unit.toFixed(0)}` : `−₹${Math.abs(savings_per_unit).toFixed(0)}`,
              color: impactColor,
              icon: <Award size={13} />,
            },
            {
              label: "Delivery",
              value: `${recommended.delivery_days} days`,
              color: "var(--brand)",
              icon: <Clock size={13} />,
            },
          ].map(m => (
            <div key={m.label} className="sourcing-metric">
              <div className="sourcing-metric-label">{m.label}</div>
              <div className="sourcing-metric-val" style={{ color: m.color, display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}>
                {m.icon}{m.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Comparison table */}
      <div className="sourcing-table-wrap">
        <table className="sourcing-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Country</th>
              <th>Unit Cost</th>
              <th>Logistics</th>
              <th>Tax/Duty</th>
              <th>Landed Cost</th>
              <th>Delivery</th>
              <th>Quality</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {allOptions.map((opt, i) => {
              const isRec = opt.country === recommended.country && opt.option_type === recommended.option_type;
              const tc = TYPE_COLORS[opt.option_type] || TYPE_COLORS.local;
              const flag = COUNTRY_FLAGS[opt.country] || "🌐";
              return (
                <tr key={i} className={isRec ? "recommended-row" : ""}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {isRec && <CheckCircle size={14} color="#0284c7" />}
                      <span className="sourcing-type-chip" style={{
                        background: tc.bg, color: tc.text, border: `1px solid ${tc.border}`,
                      }}>
                        {opt.option_type.replace("_", " ").replace(/^\w/, c => c.toUpperCase())}
                      </span>
                    </div>
                    {isRec && (
                      <div style={{ fontSize: ".63rem", color: "var(--brand)", fontWeight: 700, marginTop: 4, display: "flex", alignItems: "center", gap: 3 }}>
                        <Star size={10} fill="#0284c7" /> Recommended
                      </div>
                    )}
                  </td>
                  <td>
                    <span className="country-flag">{flag}</span>
                    <span style={{ fontWeight: 600, color: "var(--t1)" }}>{opt.country}</span>
                  </td>
                  <td style={{ fontFamily: "var(--mono)", fontWeight: 700, color: "var(--t1)" }}>
                    ₹{opt.cost_per_unit.toLocaleString()}
                  </td>
                  <td style={{ fontFamily: "var(--mono)", color: "var(--t2)" }}>
                    ₹{opt.logistics_cost.toLocaleString()}
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, color: opt.tax_rate > 0 ? "var(--am)" : "var(--em)" }}>
                      {opt.tax_rate}%
                    </span>
                  </td>
                  <td style={{ fontFamily: "var(--mono)", fontWeight: 800, color: isRec ? "var(--brand)" : "var(--t1)" }}>
                    ₹{opt.total_landed_cost.toLocaleString()}
                  </td>
                  <td>
                    <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                      <Clock size={12} color="var(--t3)" />
                      <span style={{ fontWeight: 600, color: opt.delivery_days <= 10 ? "var(--em)" : opt.delivery_days <= 21 ? "var(--am)" : "var(--rose)" }}>
                        {opt.delivery_days}d
                      </span>
                    </span>
                  </td>
                  <td><QualityDots score={opt.quality_score} /></td>
                  <td style={{ minWidth: 140 }}>
                    <ScoreBar score={opt.weighted_score} color={tc.bar} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Strategy impact note — concise one-liner */}
      <div className="sourcing-reasoning-box">
        <div style={{ fontWeight: 700, color: "var(--brand)", fontSize: ".75rem", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 6 }}>
          💡 Sourcing Impact
        </div>
        <p style={{ margin: 0, fontSize: ".85rem", lineHeight: 1.6 }}>{strategy_note}</p>
      </div>
    </div>
  );
}
