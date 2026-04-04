import { useState, useEffect } from "react";
import { Globe, Package, Zap } from "lucide-react";
import SourcingTable from "../components/SourcingTable";
import { api } from "../services/api";

const COUNTRIES = [
  "India", "USA", "UK", "UAE", "Germany", "France", "Singapore",
  "Japan", "Canada", "Australia", "China", "Brazil", "Mexico",
  "South Africa", "Netherlands", "Italy"
];

const COUNTRY_FLAGS = {
  India:"🇮🇳", USA:"🇺🇸", UK:"🇬🇧", UAE:"🇦🇪", Germany:"🇩🇪",
  France:"🇫🇷", Singapore:"🇸🇬", Japan:"🇯🇵", Canada:"🇨🇦",
  Australia:"🇦🇺", China:"🇨🇳", Brazil:"🇧🇷", Mexico:"🇲🇽",
  "South Africa":"🇿🇦", Netherlands:"🇳🇱", Italy:"🇮🇹",
};

const SAMPLE_PRODUCTS = [
  { name:"Industrial Control Valves", cost:850 },
  { name:"Hydraulic Pressure Sensors", cost:3200 },
  { name:"Servo Motor Drive Units",   cost:7500 },
  { name:"Solar Panel Modules",       cost:4200 },
  { name:"Industrial Pumps",          cost:12000 },
];

export default function SourcingPage() {
  const [product,   setProduct]   = useState("");
  const [country,   setCountry]   = useState("USA");
  const [quantity,  setQuantity]  = useState(100);
  const [costPU,    setCostPU]    = useState(1000);
  const [loading,   setLoading]   = useState(false);
  const [sourcing,  setSourcing]  = useState(null);
  const [error,     setError]     = useState(null);

  const analyze = async () => {
    if (!product.trim()) { setError("Please enter a product name."); return; }
    if (costPU <= 0)     { setError("Cost per unit must be positive."); return; }
    setLoading(true); setError(null); setSourcing(null);
    try {
      const data = await api.getSourcing(product, country, quantity, costPU);
      setSourcing(data);
    } catch (e) {
      setError(e.message || "Sourcing analysis failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const loadSample = (s) => {
    setProduct(s.name);
    setCostPU(s.cost);
  };

  return (
    <>
      {/* Header */}
      <div className="page-header page-header-row">
        <div>
          <h1>🌍 Global Sourcing Engine</h1>
          <p>Compare Local · Offshore · Near-Client supply chains with intelligent weighted scoring</p>
        </div>
        <span className="badge badge-indigo" style={{ fontSize: ".8rem", padding: "6px 16px" }}>
          AI Powered
        </span>
      </div>

      {/* Input Panel — full width */}
      <div className="card mb-md" style={{ borderRadius: "var(--r-2xl)" }}>
        <div className="card-header">
          <span className="card-title"><Package size={13} /> Sourcing Parameters</span>
        </div>

        {/* Quick samples */}
        <div style={{ marginBottom: 18 }}>
          <div className="form-label">Quick Sample Products</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {SAMPLE_PRODUCTS.map(s => (
              <button key={s.name} className="btn btn-ghost btn-sm"
                style={{ borderRadius: "var(--r-full)", border: "1px solid var(--br)", fontSize: ".75rem" }}
                onClick={() => loadSample(s)}>
                {s.name}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 14, alignItems: "end" }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Product / Material Name</label>
            <input className="input" placeholder="e.g. Industrial Control Valves"
              value={product} onChange={e => setProduct(e.target.value)} />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Client Country</label>
            <select className="input" value={country} onChange={e => setCountry(e.target.value)}>
              {COUNTRIES.map(c => (
                <option key={c} value={c}>{COUNTRY_FLAGS[c] || "🌐"} {c}</option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Quantity (units)</label>
            <input className="input" type="number" min={1} value={quantity}
              onChange={e => setQuantity(Number(e.target.value))} />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Internal Cost (₹/unit)</label>
            <input className="input" type="number" min={1} value={costPU}
              onChange={e => setCostPU(Number(e.target.value))} />
          </div>
        </div>

        <button className="btn btn-primary btn-lg" onClick={analyze} disabled={loading}
          style={{ marginTop: 18, minWidth: 220 }}>
          {loading
            ? <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Analysing…</>
            : <><Globe size={16} /> Analyse Global Sourcing</>}
        </button>

        {error && (
          <div className="alert alert-error" style={{ marginTop: 16 }}>
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {sourcing && (
        <div>
          <div className="section-divider">
            <div className="section-divider-line" />
            <div className="section-divider-label"><Globe size={11} style={{ verticalAlign: "middle", marginRight: 4 }} />Sourcing Analysis Results</div>
            <div className="section-divider-line" />
          </div>

          <div className="card" style={{ borderRadius: "var(--r-2xl)" }}>
            <SourcingTable sourcing={sourcing} />
          </div>

          {/* Recommendation summary */}
          <div className="card" style={{ borderRadius: "var(--r-2xl)", marginTop: 18 }}>
            <div className="card-header">
              <span className="card-title"><Zap size={13} /> Recommended Source Summary</span>
              <span className="badge badge-indigo">Score {sourcing.recommended.weighted_score.toFixed(0)}/100</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
              {[
                { label: "Sourced From",    value: sourcing.recommended.region_label,          icon: "🏆" },
                { label: "Landed Cost",     value: `₹${sourcing.recommended.total_landed_cost.toLocaleString()}/unit`, icon: "💰" },
                { label: "Quality Rating",  value: `${Math.round(sourcing.recommended.quality_score * 100)}%`, icon: "⭐" },
                { label: "Lead Time",       value: `${sourcing.recommended.delivery_days} days`, icon: "⏱️" },
                { label: "Import Duty",     value: `${sourcing.recommended.tax_rate}%`,         icon: "🏛️" },
                { label: "Cost Savings",    value: sourcing.savings_per_unit > 0 ? `₹${sourcing.savings_per_unit.toFixed(0)}/unit (${Math.abs(sourcing.cost_impact_percent)}% reduction)` : `No savings vs baseline`, icon: "📉" },
              ].map(r => (
                <div key={r.label} className="result-row" style={{ padding: "10px 0" }}>
                  <span className="rl">{r.icon} {r.label}</span>
                  <span className="rv">{r.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
