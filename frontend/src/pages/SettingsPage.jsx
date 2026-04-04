import { useState } from "react";
import { Settings, Save, CheckCircle } from "lucide-react";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    apiKey: "",
    defaultStrategy: "balanced",
    companyName: "TechFlow Industries Pvt Ltd",
    currency: "INR",
    taxRate: "18",
  });
  const [saved, setSaved] = useState(false);

  const handleChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = () => {
    // In a real app, this would persist to backend
    localStorage.setItem("intelliquote_settings", JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Configure your IntelliQuote preferences</p>
      </div>

      <div style={{ maxWidth: "640px" }}>
        <div className="card mb-lg">
          <div className="card-header">
            <span className="card-title">
              <Settings size={16} style={{ marginRight: "6px" }} />
              General Settings
            </span>
          </div>

          <div className="form-group">
            <label className="form-label">Company Name</label>
            <input
              className="input"
              value={settings.companyName}
              onChange={(e) => handleChange("companyName", e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Default Strategy Mode</label>
            <select
              className="select"
              value={settings.defaultStrategy}
              onChange={(e) => handleChange("defaultStrategy", e.target.value)}
            >
              <option value="aggressive">Aggressive — Win at all costs</option>
              <option value="balanced">Balanced — Optimal trade-off</option>
              <option value="premium">Premium — Maximize margins</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Default Currency</label>
            <select
              className="select"
              value={settings.currency}
              onChange={(e) => handleChange("currency", e.target.value)}
            >
              <option value="INR">INR (₹) — Indian Rupee</option>
              <option value="USD">USD ($) — US Dollar</option>
              <option value="EUR">EUR (€) — Euro</option>
              <option value="GBP">GBP (£) — British Pound</option>
              <option value="AED">AED — UAE Dirham</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Default Tax Rate (%)</label>
            <input
              className="input"
              type="number"
              value={settings.taxRate}
              onChange={(e) => handleChange("taxRate", e.target.value)}
            />
            <span className="form-hint">Applied as default for domestic orders</span>
          </div>
        </div>

        <div className="card mb-lg">
          <div className="card-header">
            <span className="card-title">🔑 API Configuration</span>
          </div>

          <div className="form-group">
            <label className="form-label">LLM API Key (Optional override)</label>
            <input
              className="input"
              type="password"
              placeholder="Leave empty to use server-side key"
              value={settings.apiKey}
              onChange={(e) => handleChange("apiKey", e.target.value)}
            />
            <span className="form-hint">
              The backend uses Gemini API by default. Override here for custom deployments.
            </span>
          </div>
        </div>

        <button className="btn btn-primary btn-lg" onClick={handleSave}>
          {saved ? (
            <>
              <CheckCircle size={18} /> Saved!
            </>
          ) : (
            <>
              <Save size={18} /> Save Settings
            </>
          )}
        </button>
      </div>
    </div>
  );
}
