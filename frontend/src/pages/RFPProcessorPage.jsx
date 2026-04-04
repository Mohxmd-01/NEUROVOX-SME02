import { useState, useEffect, useRef, useCallback } from "react";
import {
  FileText, Zap, TrendingUp, Users, Brain, BookOpen,
  ChevronDown, ChevronUp, Download, AlertTriangle,
  CheckCircle, Target, Shield, BarChart3, Globe,
  Lightbulb, SlidersHorizontal, Upload, X, ThumbsUp,
  BarChart2, AlertCircle, Award, Star, Info, Package, MapPin,
} from "lucide-react";
import { api } from "../services/api";
import StrategyComparisonTable from "../components/StrategyComparisonTable";
import NegotiationPanel        from "../components/NegotiationPanel";
import FeedbackModal           from "../components/FeedbackModal";
import SourcingTable           from "../components/SourcingTable";

const SAMPLE_DOMESTIC = `Dear TechFlow Industries,

We require a quotation for Industrial Control Valves for our plant expansion.
- Product: Industrial Control Valves (Gate type, SS304)
- Quantity: 500 units
- Delivery: Within 14 days to Mumbai warehouse
- Budget: Approximately ₹1100 per unit
- Requirements: ISO certification, free installation support preferred

We have been evaluating 3 vendors. Please submit your competitive quotation.

Regards, Rajesh Kumar — Procurement Manager, Acme Corp India`;

const SAMPLE_INTL = `Dear TechFlow Industries,

We require a quotation for Hydraulic Pressure Sensors for our Texas facility.
- Product: Hydraulic Pressure Sensors
- Quantity: 200 units
- Delivery: 21 days, Houston TX
- Budget: ~$450 per unit
- Certifications: CE, UL listed preferred

Please quote in USD with full warranty terms.

Best regards, James Carter — VP Procurement, Meridian Industrial USA`;

const STEPS = [
  { id:"parse",     label:"Parsing RFP",        icon:FileText },
  { id:"knowledge", label:"Knowledge Recall",    icon:BookOpen },
  { id:"pricing",   label:"Internal Pricing",    icon:TrendingUp },
  { id:"sourcing",  label:"Sourcing Analysis",   icon:Globe },
  { id:"compete",   label:"Competitor Analysis", icon:Users },
  { id:"strategy",  label:"AI Strategy",         icon:Brain },
];

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

export default function RFPProcessorPage() {
  const [tab,       setTab]       = useState("text");
  const [rfpText,   setRfpText]   = useState("");
  const [pdfFile,   setPdfFile]   = useState(null);
  const [extracting,setExtracting]= useState(false);
  const [dragOver,  setDragOver]  = useState(false);
  const [stratMode, setStratMode] = useState("balanced");
  const [loading,   setLoading]   = useState(false);
  const [activeStep,setActiveStep]= useState(-1);
  const [result,    setResult]    = useState(null);
  const [pdfStatus, setPdfStatus] = useState(null);
  const [whyOpen,   setWhyOpen]   = useState(false);
  const [error,     setError]     = useState(null);
  const [strategies,setStrategies]= useState(null);
  const [stratLoad, setStratLoad] = useState(false);
  const [simOn,     setSimOn]     = useState(false);
  const [simAdj,    setSimAdj]    = useState(0);
  const [simData,   setSimData]   = useState(null);
  const [showFb,    setShowFb]    = useState(false);
  const [fbOutcome, setFbOutcome] = useState(null);
  const fileRef = useRef(null);
  const [downloading, setDownloading] = useState(false);
  const [countries,   setCountries]   = useState([]);
  const [country,     setCountry]     = useState("");  // empty = auto-detect
  const [taxPreview,  setTaxPreview]  = useState(null);

  // Load countries on mount
  useEffect(() => {
    api.getCountries().then(setCountries).catch(() => setCountries([]));
  }, []);

  // Live tax preview when country changes
  useEffect(() => {
    if (!country) { setTaxPreview(null); return; }
    api.getTaxRate(country, result?.parsed_rfp?.product || null)
      .then(setTaxPreview)
      .catch(() => setTaxPreview(null));
  }, [country, result?.parsed_rfp?.product]);

  useEffect(() => {
    if (!loading) { setActiveStep(-1); return; }
    let s = 0; setActiveStep(0);
    const iv = setInterval(() => { s = Math.min(s+1, STEPS.length-1); setActiveStep(s); }, 1100);
    return () => clearInterval(iv);
  }, [loading]);

  const handlePDF = async (file) => {
    if (!file?.name?.toLowerCase().endsWith(".pdf")) { setError("Please upload a valid PDF file."); return; }
    setPdfFile(file); setExtracting(true); setError(null);
    try { const r = await api.extractPDF(file); setRfpText(r.text); setTab("text"); }
    catch (e) { setError(e.message||"Failed to extract PDF text."); }
    finally { setExtracting(false); }
  };

  const process = async () => {
    if (!rfpText.trim()) return;
    setLoading(true); setError(null); setResult(null);
    setPdfStatus(null); setSimOn(false); setSimAdj(0); setSimData(null);
    setStrategies(null); setFbOutcome(null);
    try {
      const data = await api.processRFP(rfpText, stratMode, country || null);
      setResult(data);
      setWhyOpen(false);
      // Auto-set country from detected if not manually overridden
      if (!country && data.geo?.country) setCountry(data.geo.country);
      loadStrats(data.quote_id);
    } catch (e) { setError(e.message||"Processing failed. Check backend connection."); }
    finally { setLoading(false); }
  };

  const loadStrats = async (qid) => {
    setStratLoad(true);
    try { setStrategies(await api.getStrategies(null, qid)); } catch {}
    finally { setStratLoad(false); }
  };

  const runSim = useCallback(async (adj) => {
    if (!result) return;
    const base = result.summary?.final_price || result.strategy?.final_price;
    const cost = result.pricing?.cost_per_unit;
    const comp = result.competitor?.competitor_price;
    if (!base || !cost) return;
    try {
      const r = await api.simulate(base+adj, cost, comp);
      setSimData(r.scenarios?.find(s=>s.adjustment===0) || r.scenarios?.[Math.floor(r.scenarios.length/2)]);
    } catch {
      const price = base+adj;
      const margin = ((price-cost)/cost)*100;
      let win = 60;
      if (price < comp*0.9) win=90; else if (price<comp) win=73; else if (price<comp*1.1) win=48; else win=25;
      setSimData({ price:price.toFixed(2), adjustment:adj, margin_percent:margin.toFixed(1), win_probability:win, risk:margin>15?"low":margin>8?"medium":"high" });
    }
  }, [result]);

  useEffect(() => { if (simOn && result) runSim(simAdj); }, [simAdj, simOn, runSim, result]);

  const handleDownloadPDF = async () => {
    if (!result?.quote_id) return;
    setDownloading(true); setPdfStatus("generating");
    try {
      await api.generateAndDownloadPDF(result.quote_id);
      setPdfStatus("done");
    } catch (e) {
      setPdfStatus("error");
      setError("PDF generation failed: " + (e.message || "Unknown error"));
    } finally {
      setDownloading(false);
    }
  };

  const s         = result?.strategy || {};
  const summary   = result?.summary  || {};
  const geo       = result?.geo      || {};
  const finalPrice = summary.final_price || s.final_price;
  const winProb   = summary.win_probability || s.win_probability || "~60%";
  const risk      = summary.risk_level || s.risk_level || "medium";
  const stType    = summary.strategy || s.strategy_type || "balanced";
  const confPct   = result?.confidence_score != null ? Math.round(result.confidence_score*100) : null;
  const insights  = result?.insights || s.insights || [];
  const valueAdds = result?.value_additions || s.value_additions || [];
  const tactics   = result?.negotiation_tactics || s.negotiation_tactics || [];

  // Currency display helpers
  const sym       = geo.currency_symbol || "₹";
  const isIntl    = geo.is_international || false;
  const localSym  = result?.currency?.symbol  || sym;
  const localConverted = result?.currency?.converted;
  // unit_currency: per-unit conversion for the final price
  const unitConverted  = result?.unit_currency?.converted;
  const unitSym        = result?.unit_currency?.symbol || localSym;

  // Internal TechFlow prices are ALWAYS in INR (our cost, competitor data, etc.)
  const fmtInr   = (val) => val != null ? `₹${Number(val).toLocaleString()}` : "—";
  // Converted local currency (USD/GBP etc) — only for international totals
  const fmtLocal = (val) => val != null ? `${localSym}${Number(val).toLocaleString()}` : "—";
  // Smart: show INR for domestic, local currency for international
  const fmtPrice = (val) => isIntl ? fmtLocal(val) : fmtInr(val);


  return (
    <>
      {/* Header */}
      <div className="page-header page-header-row">
        <div>
          <h1>RFP Decision Engine</h1>
          <p>Paste or upload an RFP — AI detects location, tax, currency automatically</p>
        </div>
        <div style={{ display:"flex", gap:8 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => { setRfpText(SAMPLE_DOMESTIC); setTab("text"); setCountry(""); }}>🇮🇳 India Sample</button>
          <button className="btn btn-ghost btn-sm" onClick={() => { setRfpText(SAMPLE_INTL); setTab("text"); setCountry(""); }}>🇺🇸 USA Sample</button>
        </div>
      </div>

      {/* Input card */}
      <div className="card mb-md">
        <div className="card-header">
          <span className="card-title"><FileText size={13}/> RFP Input</span>
        </div>

        {/* Tab switcher */}
        <div className="tabs-bar">
          <button className={`tab-btn ${tab==="text"?"active":""}`} onClick={() => setTab("text")}><FileText size={13}/> Paste Text</button>
          <button className={`tab-btn ${tab==="pdf"?"active":""}`}  onClick={() => setTab("pdf")}><Upload size={13}/> Upload PDF</button>
        </div>

        {tab === "text" ? (
          <textarea className="textarea" rows={8}
            placeholder={"Paste your RFP text here…\n\nInclude: product, quantity, deadline, budget, and client details for best results."}
            value={rfpText} onChange={e => setRfpText(e.target.value)} />
        ) : (
          <div>
            <div className={`drop-zone ${dragOver?"drag-over":""}`}
              onDragOver={e=>{e.preventDefault();setDragOver(true)}} onDragLeave={()=>setDragOver(false)}
              onDrop={e=>{e.preventDefault();setDragOver(false);handlePDF(e.dataTransfer.files[0])}}
              onClick={()=>fileRef.current?.click()}>
              <input ref={fileRef} type="file" accept=".pdf" style={{display:"none"}} onChange={e=>handlePDF(e.target.files[0])} />
              <div className="drop-zone-icon">
                {extracting ? <div className="spinner" style={{width:20,height:20,borderWidth:2}}/> : <Upload size={20}/>}
              </div>
              <div className="drop-zone-title">{extracting ? "Extracting text from PDF…" : "Drop PDF here or click to browse"}</div>
              <div className="drop-zone-sub">{extracting ? "Please wait…" : "PDF files only — text extracted automatically"}</div>
            </div>
            {pdfFile && !extracting && (
              <div style={{display:"flex",alignItems:"center",gap:10,marginTop:10,padding:"10px 14px",background:"var(--em-dim)",border:"1px solid var(--em-br)",borderRadius:"var(--r-md)"}}>
                <CheckCircle size={14} style={{color:"var(--em-lt)",flexShrink:0}} />
                <span style={{fontSize:".83rem",color:"var(--t1)",fontWeight:500,flex:1}}>{pdfFile.name}</span>
                <span style={{fontSize:".75rem",color:"var(--t3)"}}>{rfpText.length} chars</span>
                <button className="btn btn-ghost btn-sm" style={{padding:"3px 6px"}} onClick={e=>{e.stopPropagation();setPdfFile(null);setRfpText("");}}>
                  <X size={12}/>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Strategy + Country Row */}
        <div style={{ marginTop:18, display:"grid", gridTemplateColumns:"1fr 1fr", gap:18, alignItems:"start" }}>
          {/* Strategy selector */}
          <div>
            <div className="form-label" style={{ marginBottom:8 }}>Pricing Strategy</div>
            <div className="strat-toggle">
              {[
                { id:"aggressive", label:"Aggressive", icon:<Target size={13}/> },
                { id:"balanced",   label:"Balanced",   icon:<BarChart3 size={13}/> },
                { id:"premium",    label:"Premium",    icon:<Shield size={13}/> },
              ].map(m => (
                <button key={m.id} className={`strat-btn ${stratMode===m.id?`strat-active-${m.id}`:""}`} onClick={() => setStratMode(m.id)}>
                  {m.icon} {m.label}
                </button>
              ))}
            </div>
          </div>

          {/* Country override */}
          <div>
            <div className="form-label" style={{ marginBottom:8 }}>
              <MapPin size={11} style={{verticalAlign:"middle",marginRight:4}}/>
              Client Country
              {!country && <span style={{fontSize:".7rem",color:"var(--t3)",marginLeft:8,fontWeight:400}}>Auto-detect from RFP</span>}
            </div>
            <select
              className="input"
              value={country}
              onChange={e => setCountry(e.target.value)}
              style={{fontSize:".88rem"}}
            >
              <option value="">🌐 Auto-detect from RFP</option>
              {countries.map(c => (
                <option key={c.country} value={c.country}>
                  {COUNTRY_FLAGS[c.country] || "🌐"} {c.country} — {c.tax_name} {c.rate}% · {c.currency}
                </option>
              ))}
            </select>
            {taxPreview && (
              <div style={{marginTop:7,display:"flex",gap:8,flexWrap:"wrap"}}>
                <span className="badge badge-indigo" style={{fontSize:".73rem"}}>
                  {taxPreview.tax_name} {taxPreview.rate}%
                </span>
                <span className="badge badge-cyan" style={{fontSize:".73rem"}}>
                  {taxPreview.currency} · {taxPreview.symbol?.trim()}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* CTA */}
        <div style={{ marginTop:18, display:"flex", alignItems:"center", gap:12, flexWrap:"wrap" }}>
          <button className="btn btn-primary btn-lg" onClick={process} disabled={loading || !rfpText.trim()}>
            {loading ? <><div className="spinner" style={{width:16,height:16,borderWidth:2}}/> Analysing…</> : <><Zap size={16}/> Get AI Decision</>}
          </button>
          {!rfpText.trim() && <span style={{fontSize:".8rem",color:"var(--t3)"}}>↑ Paste or upload an RFP to start</span>}
          {country && result && (
            <button className="btn btn-ghost btn-sm" onClick={() => setCountry("")} title="Reset to auto-detect">
              <X size={12}/> Reset Country
            </button>
          )}
        </div>

        {/* Pipeline */}
        {loading && (
          <div style={{ marginTop:22 }}>
            <div style={{ fontSize:".72rem", color:"var(--t3)", fontWeight:700, textTransform:"uppercase", letterSpacing:".05em", marginBottom:12 }}>AI Pipeline Running…</div>
            <div className="pipeline">
              {STEPS.map((step, i) => {
                const Icon = step.icon;
                const state = i < activeStep ? "done" : i === activeStep ? "active" : "";
                return (
                  <div key={step.id} className={`pipe-step ${state}`}>
                    <div className="pipe-dot">
                      {i < activeStep ? <CheckCircle size={14}/> : i===activeStep ? <div className="spinner" style={{width:13,height:13,borderWidth:2}}/> : <Icon size={12}/>}
                    </div>
                    <div className="pipe-label">{step.label}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="alert alert-error mb-md">
          <AlertTriangle size={16}/> <span><strong>Error: </strong>{error}</span>
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Decision banner */}
          <div className="decision-banner mb-md">
            <div>
              <div className="banner-price-label">Recommended Price (INR)</div>
              <div className="banner-price-val">₹{finalPrice?.toLocaleString()}</div>
              <div className="banner-price-sub">per unit · internal base price</div>
            </div>
            {isIntl && unitConverted && (
              <div>
                <div className="banner-price-label">Client Price ({geo.currency})</div>
                <div className="banner-price-val" style={{color:"var(--brand-lt)",fontSize:"1.6rem"}}>{unitSym}{Number(unitConverted).toLocaleString()}</div>
                <div className="banner-price-sub">per unit · live exchange rate</div>
              </div>
            )}

            <div className="banner-metric">
              <div className="banner-metric-label">Strategy</div>
              <span className={`badge ${STRAT_BADGE[stType]||"badge-indigo"}`} style={{fontSize:".88rem",padding:"5px 14px"}}>{stType}</span>
            </div>
            <div className="banner-metric">
              <div className="banner-metric-label">Win Probability</div>
              <div className="banner-metric-val em">{winProb}</div>
            </div>
            <div className="banner-metric">
              <div className="banner-metric-label">Risk</div>
              <span className={`badge ${risk==="low"?"badge-green":risk==="high"?"badge-rose":"badge-amber"}`} style={{fontSize:".9rem",padding:"5px 14px"}}>{risk}</span>
            </div>
            {confPct !== null && (
              <div className="banner-metric">
                <div className="banner-metric-label">Confidence</div>
                <div className="banner-metric-val cy">{confPct}%</div>
              </div>
            )}
            {result.past_cases_used > 0 && (
              <div className="banner-note">
                <Brain size={12}/> Informed by {result.past_cases_used} past case{result.past_cases_used>1?"s":""}
              </div>
            )}
          </div>

          {/* Geo + Tax Card */}
          {result.geo && (
            <div className="geo-card mb-md">
              <div className="card-header" style={{marginBottom:12}}>
                <span className="card-title"><Globe size={13}/> Location & Tax</span>
                <span className={`badge ${isIntl?"badge-amber":"badge-green"}`}>
                  {COUNTRY_FLAGS[geo.country] || "🌐"} {geo.country} · {isIntl ? "International" : "Domestic"}
                </span>
              </div>
              <div className="geo-metrics">
                {[
                  { l:"Currency",               v:`${geo.currency} (${geo.currency_symbol?.trim()})` },
                  { l:"Tax Type",               v:geo.tax_name || "—" },
                  { l:"Tax Rate",               v:`${geo.tax_rate}%` },
                  { l:"Tax Amount (INR)",        v:`₹${Number(geo.tax_amount||0).toLocaleString()}` },
                  { l:"Subtotal excl. tax (INR)",v:`₹${Number(geo.subtotal_inr||0).toLocaleString()}` },
                  { l:"Grand Total INR",         v:`₹${Number(geo.grand_total_inr||0).toLocaleString()}`, highlight:true },
                  ...(isIntl && localConverted ? [{ l:`Client Invoice (${geo.currency})`, v:`${localSym}${Number(localConverted).toLocaleString()}`, highlight:true }] : []),
                ].map(item => (
                  <div key={item.l} className="geo-metric">
                    <div className="geo-metric-label">{item.l}</div>
                    <div className="geo-metric-val" style={item.highlight ? {color:"var(--brand-lt)",fontWeight:800} : {}}>{item.v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}


          {/* Strategy Comparison */}
          <div className="section-divider">
            <div className="section-divider-line"/>
            <div className="section-divider-label"><BarChart2 size={11} style={{verticalAlign:"middle",marginRight:4}}/>Strategy Comparison</div>
            <div className="section-divider-line"/>
          </div>
          {stratLoad ? (
            <div className="loading-row mb-md"><div className="spinner"/> Loading strategy comparison…</div>
          ) : strategies ? (
            <StrategyComparisonTable strategies={strategies} recommended={strategies.recommended} geo={geo} currencyRate={result?.unit_currency}/>
          ) : null}

          {/* Global Sourcing */}
          {result.sourcing && (
            <>
              <div className="section-divider">
                <div className="section-divider-line"/>
                <div className="section-divider-label"><Globe size={11} style={{verticalAlign:"middle",marginRight:4}}/> Global Sourcing Analysis</div>
                <div className="section-divider-line"/>
              </div>
              <div className="card mb-md" style={{borderRadius:"var(--r-2xl)"}}>
                <div className="card-header">
                  <span className="card-title"><Package size={13}/> Sourcing Intelligence</span>
                  <span className="badge badge-indigo">3 Options Evaluated</span>
                </div>
                <SourcingTable sourcing={result.sourcing} />
              </div>
            </>
          )}

          {/* Data cards */}
          <div className="results-grid mb-md">
            {/* RFP Card */}
            <div className="result-card">
              <div className="result-card-title"><FileText size={13} style={{color:"var(--brand-lt)"}}/> What Was Asked</div>
              {[
                { l:"Product",  v:result.parsed_rfp?.product },
                { l:"Quantity", v:`${result.parsed_rfp?.quantity?.toLocaleString()} units` },
                { l:"Deadline", v:result.parsed_rfp?.deadline },
                { l:"Client",   v:result.parsed_rfp?.client_name||"Unknown" },
                { l:"Market",   v:`${COUNTRY_FLAGS[result.parsed_rfp?.client_country]||""} ${result.parsed_rfp?.client_country||"—"}` },
                ...(result.parsed_rfp?.budget_hint ? [{ l:"Budget Hint", v:result.parsed_rfp.budget_hint }] : []),
              ].map(row => <div key={row.l} className="result-row"><span className="rl">{row.l}</span><span className="rv">{row.v}</span></div>)}
              {result.parsed_rfp?.special_requirements?.length > 0 && (
                <div style={{marginTop:10}}>
                  <span className="rl" style={{display:"block",marginBottom:6}}>Special Reqs</span>
                  <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
                    {result.parsed_rfp.special_requirements.map((r,i)=><span key={i} className="badge badge-cyan">{r}</span>)}
                  </div>
                </div>
              )}
            </div>

            {/* Market Card — always INR (internal TechFlow catalog data) */}
            <div className="result-card">
              <div className="result-card-title"><TrendingUp size={13} style={{color:"var(--em-lt)"}}/> Market Comparison <span style={{fontSize:".7rem",color:"var(--t3)",fontWeight:400,marginLeft:6}}>— Internal INR</span></div>
              {[
                { l:"Our Cost/Unit",    v:fmtInr(result.pricing?.cost_per_unit) },
                { l:"Base List Price",  v:fmtInr(result.pricing?.base_price) },
                { l:"Min Margin",       v:`${result.pricing?.min_margin_percent}%` },
                { l:"Bulk Discount",    v:`${result.pricing?.bulk_discount_percent}%`, green:true },
                { l:"Competitor Price", v:fmtInr(result.competitor?.competitor_price), red:true },
                { l:"Market Average",   v:fmtInr(result.competitor?.market_avg) },
                { l:"Market Range",     v:`${fmtInr(result.competitor?.market_low)} – ${fmtInr(result.competitor?.market_high)}` },
              ].map(row => (
                <div key={row.l} className="result-row">
                  <span className="rl">{row.l}</span>
                  <span className={`rv ${row.green?"green":""}`} style={row.red?{color:"var(--rose)"}:{}}>{row.v}</span>
                </div>
              ))}
              <div className="comp-chart">
                {[
                  { l:"Our Price",    v:finalPrice,                         col:"var(--brand-lt)" },
                  { l:"Competitor",   v:result.competitor?.competitor_price, col:"var(--rose)" },
                  { l:"Market Avg",   v:result.competitor?.market_avg,       col:"var(--t3)" },
                ].map((bar,i) => {
                  const mx = result.competitor?.market_high||1;
                  const pct = Math.min((bar.v/mx)*100,100);
                  return (
                    <div key={i} className="comp-bar">
                      <span className="comp-bar-val" style={{color:bar.col}}>{fmtInr(bar.v)}</span>
                      <div className="comp-bar-track"><div className="comp-bar-fill" style={{height:`${pct}%`,background:bar.col}}/></div>
                      <span className="comp-bar-lbl">{bar.l}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* AI Decision — show in local currency for international */}
            <div className="result-card" style={{borderColor:"var(--brand-br)"}}>
              <div className="result-card-title"><Brain size={13} style={{color:"var(--brand-lt)"}}/> AI Decision</div>
              {[
                { l:"Price (INR)",    v:fmtInr(s.final_price), cls:"big" },
                ...(isIntl && unitConverted ? [{ l:`Price (${geo.currency})`, v:`${unitSym}${Number(unitConverted).toLocaleString()}`, cls:"big", highlight:true }] : []),
                { l:"Strategy",    badge:true, bc:STRAT_BADGE[stType]||"badge-indigo", bv:stType },
                { l:"Margin",      v:`${s.margin_percent}%`, cls:"green" },
                { l:"Risk",        badge:true, bc:risk==="low"?"badge-green":risk==="high"?"badge-rose":"badge-amber", bv:risk },
                { l:"Win Prob",    v:winProb, cls:"green" },
                ...(confPct!==null?[{ l:"Confidence", v:`${confPct}%` }]:[]),
              ].map(row => (
                <div key={row.l} className="result-row">
                  <span className="rl">{row.l}</span>
                  {row.badge
                    ? <span className={`badge ${row.bc}`}>{row.bv}</span>
                    : <span className={`rv ${row.cls||""}`} style={row.highlight?{color:"var(--brand-lt)",fontWeight:800}:{}}>{row.v}</span>}
                </div>
              ))}
            </div>

            {/* Financials */}
            <div className="result-card">
              <div className="result-card-title"><BarChart3 size={13} style={{color:"var(--am-lt)"}}/> Financials</div>
              {result.tax && [
                { l:"Unit Price (INR)",                                   v:fmtInr(s.final_price) },
                { l:`${result.tax.tax_name} @ ${result.tax.tax_rate}%`, v:fmtInr(result.tax.tax_amount) },
              ].map(row=><div key={row.l} className="result-row"><span className="rl">{row.l}</span><span className="rv">{row.v}</span></div>)}
              {result.tax && (
                <div className="result-row" style={{marginTop:4,paddingTop:12,borderTop:"2px solid var(--br)"}}>
                  <span style={{fontWeight:700,color:"var(--t1)"}}>Grand Total (incl. tax)</span>
                  <span className="rv big">{fmtInr(result.tax.total)}</span>
                </div>
              )}
              {isIntl && localConverted && (
                <div className="result-row" style={{marginTop:6,paddingTop:10,borderTop:"1px dashed var(--br)"}}>
                  <span className="rl" style={{fontWeight:700}}>Client Invoice ({geo.currency})</span>
                  <span className="rv" style={{color:"var(--brand-lt)",fontWeight:800,fontSize:"1rem"}}>
                    {localSym}{Number(localConverted).toLocaleString()}
                  </span>
                </div>
              )}
              {s.alternative_prices && (
                <div style={{marginTop:14}}>
                  <div style={{fontSize:".72rem",fontWeight:700,color:"var(--t3)",textTransform:"uppercase",letterSpacing:".05em",marginBottom:8}}>Alt. Prices (INR)</div>
                  <div style={{display:"flex",gap:7}}>
                    {Object.entries(s.alternative_prices).map(([mode,price])=>(
                      <div key={mode} style={{flex:1,textAlign:"center",padding:"8px 7px",background:"var(--surface-2)",borderRadius:"var(--r-md)",border:"1px solid var(--br)"}}>
                        <div style={{fontSize:".65rem",fontWeight:700,color:"var(--t3)",textTransform:"uppercase",marginBottom:2}}>{mode}</div>
                        <div style={{fontSize:".9rem",fontWeight:700,color:"var(--t1)"}}>{fmtInr(price)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>


          {/* Value additions */}
          {valueAdds.length > 0 && (
            <div className="card mb-md">
              <div className="card-header">
                <span className="card-title"><Award size={13}/> Value Additions</span>
                {summary.below_cost_pivot && <span className="badge badge-amber" style={{fontSize:".67rem"}}>Value-Pivot Package</span>}
              </div>
              <div className="va-grid">
                {valueAdds.map((va,i)=><div key={i} className="va-chip"><CheckCircle size={12}/>{va}</div>)}
              </div>
            </div>
          )}

          {/* Negotiation */}
          <NegotiationPanel tactics={tactics}/>

          {/* Key Insights */}
          {insights.length > 0 && (
            <div className="insights-box mb-md">
              <div className="card-header" style={{marginBottom:10}}>
                <span className="card-title"><Lightbulb size={13} style={{color:"var(--brand-lt)"}}/> Key Insights</span>
                {confPct!==null && <span className="badge badge-indigo" style={{fontSize:".67rem"}}>{confPct}% confidence</span>}
              </div>
              {insights.map((ins,i)=>(
                <div key={i} className="insight-row">
                  <div className="insight-dot"/><span>{ins}</span>
                </div>
              ))}
            </div>
          )}

          {/* Reasoning (collapsed by default) */}
          <div className="reasoning-panel mb-md">
            <div className="reasoning-head" onClick={() => setWhyOpen(o=>!o)}>
              <h3><Brain size={15}/> AI Reasoning</h3>
              {whyOpen ? <ChevronUp size={15}/> : <ChevronDown size={15}/>}
            </div>
            {whyOpen && (
              <div className="reasoning-body">
                <p style={{marginBottom:12}}>{result.reasoning || s.reasoning}</p>
                {result.knowledge_context?.length > 0 && (
                  <div>
                    <div style={{fontSize:".72rem",fontWeight:700,color:"var(--t3)",textTransform:"uppercase",letterSpacing:".05em",marginBottom:7,display:"flex",alignItems:"center",gap:6}}><BookOpen size={12}/> Knowledge Sources</div>
                    <div className="src-wrap">
                      {result.knowledge_context.map((kc,i)=><span key={i} className="src-chip">📄 {kc.source_document} / {kc.source_section} ({Math.round(kc.confidence*100)}%)</span>)}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Simulation */}
          <div className="card sim-panel mb-md">
            <div className="card-header" style={{marginBottom:simOn?14:0}}>
              <span className="card-title"><SlidersHorizontal size={13}/> Price Simulation</span>
              <button className={`btn btn-sm ${simOn?"btn-primary":"btn-outline"}`}
                onClick={() => { setSimOn(p=>{if(!p)runSim(simAdj);return !p;}); }}>
                {simOn ? "✓ Enabled" : "Enable"}
              </button>
            </div>
            {!simOn && <p style={{fontSize:".82rem",color:"var(--t3)",margin:0}}>Adjust price to instantly see impact on margin, win probability, and risk.</p>}
            {simOn && (
              <>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:6,fontSize:".83rem",fontWeight:500,color:"var(--t2)"}}>
                  <span>Price Adjustment</span>
                  <span style={{fontWeight:800,color:simAdj===0?"var(--t3)":simAdj>0?"var(--rose)":"var(--em-lt)"}}>
                    {simAdj>0?`+₹${simAdj}`:simAdj<0?`-₹${Math.abs(simAdj)}`:"No adjustment"}
                  </span>
                </div>
                <input type="range" className="sim-slider" min={-200} max={200} step={5} value={simAdj} onChange={e=>setSimAdj(Number(e.target.value))}/>
                <div style={{display:"flex",justifyContent:"space-between",fontSize:".7rem",color:"var(--t3)",marginBottom:12}}><span>-₹200</span><span>No change</span><span>+₹200</span></div>
                {simData && (
                  <div className="sim-metrics">
                    {[
                      { l:"Price",    v:`₹${Number(simData.price).toLocaleString()}`, col:"var(--brand-lt)" },
                      { l:"Margin",   v:`${Number(simData.margin_percent).toFixed(1)}%`, col:Number(simData.margin_percent)>15?"var(--em-lt)":Number(simData.margin_percent)>8?"var(--am-lt)":"var(--rose)" },
                      { l:"Win Prob", v:`${simData.win_probability}%`, col:"var(--em-lt)" },
                      { l:"Risk",     badge:true, bc:simData.risk==="low"?"badge-green":simData.risk==="high"?"badge-rose":"badge-amber", bv:simData.risk },
                    ].map(m=>(
                      <div key={m.l} className="sim-metric">
                        <div className="sim-metric-label">{m.l}</div>
                        {m.badge ? <div style={{marginTop:6}}><span className={`badge ${m.bc}`} style={{fontSize:".82rem",padding:"4px 10px"}}>{m.bv}</span></div>
                          : <div className="sim-metric-val" style={{color:m.col}}>{m.v}</div>}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Actions */}
          <div style={{display:"flex",gap:10,flexWrap:"wrap",alignItems:"center"}}>
            <button
              className="btn btn-em btn-lg"
              onClick={handleDownloadPDF}
              disabled={downloading}
              style={{minWidth:200}}
            >
              {downloading && pdfStatus==="generating" ? (
                <><div className="spinner" style={{width:16,height:16,borderWidth:2}}/> Generating PDF…</>
              ) : pdfStatus==="done" ? (
                <><CheckCircle size={16}/> Downloaded ✓</>
              ) : pdfStatus==="error" ? (
                <><FileText size={16}/> Retry Download</>
              ) : (
                <><Download size={16}/> Download PDF</>
              )}
            </button>
            <button className="btn btn-outline btn-lg" onClick={() => setShowFb(true)}
              style={{borderColor:fbOutcome==="won"?"var(--em-br)":fbOutcome==="lost"?"var(--rose-br)":"var(--br-md)",color:fbOutcome==="won"?"var(--em-lt)":fbOutcome==="lost"?"var(--rose)":"var(--t2)"}}>
              <ThumbsUp size={15}/> {fbOutcome ? `Outcome: ${fbOutcome}` : "Record Outcome"}
            </button>
          </div>
        </>
      )}

      {showFb && result && (
        <FeedbackModal quoteId={result.quote_id} quotePrice={finalPrice}
          onClose={() => setShowFb(false)}
          onSubmitted={o => { setFbOutcome(o); setShowFb(false); }}/>
      )}
    </>
  );
}
