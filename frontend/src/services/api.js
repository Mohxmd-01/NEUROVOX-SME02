const API_BASE = "/api";  // uses Vite proxy → http://localhost:8000/api

async function handleResponse(res) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Health check
  health: async () => {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse(res);
  },

  // Process full RFP pipeline
  processRFP: async (text, strategyMode = "balanced", countryOverride = null) => {
    const body = { text, strategy_mode: strategyMode };
    if (countryOverride) body.country_override = countryOverride;
    const res = await fetch(`${API_BASE}/process-rfp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  },

  // Get all 3 strategy variants for comparison
  getStrategies: async (rfpText = null, quoteId = null) => {
    const body = {};
    if (rfpText) body.text = rfpText;
    if (quoteId) body.quote_id = quoteId;
    const res = await fetch(`${API_BASE}/strategies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  },

  // Submit deal outcome feedback
  submitFeedback: async (quoteId, outcome, actualPrice = null, clientFeedback = null) => {
    const res = await fetch(`${API_BASE}/feedback/${quoteId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        outcome,
        actual_price: actualPrice,
        client_feedback: clientFeedback,
      }),
    });
    return handleResponse(res);
  },

  // Get feedback for a quote
  getQuoteFeedback: async (quoteId) => {
    const res = await fetch(`${API_BASE}/feedback/${quoteId}`);
    return handleResponse(res);
  },

  // Get overall win/loss stats
  getFeedbackStats: async () => {
    const res = await fetch(`${API_BASE}/feedback/stats`);
    return handleResponse(res);
  },

  // Upload PDF and extract text
  extractPDF: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/extract-pdf`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(res);
  },

  // Generate PDF for a quote
  generatePDF: async (quoteId) => {
    const res = await fetch(`${API_BASE}/generate-pdf/${quoteId}`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("PDF generation failed");
    return res.json();
  },

  // Generate and immediately download PDF as file
  generateAndDownloadPDF: async (quoteId) => {
    // Step 1: Generate the PDF on the backend
    const genRes = await fetch(`${API_BASE}/generate-pdf/${quoteId}`, { method: "POST" });
    if (!genRes.ok) throw new Error("PDF generation failed");
    // Step 2: Download the generated PDF as a blob
    const dlRes = await fetch(`${API_BASE}/download-pdf/${quoteId}`);
    if (!dlRes.ok) throw new Error("PDF download failed — " + (await dlRes.json().catch(() => ({detail: "unknown"}))).detail);
    const blob = await dlRes.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `IntelliQuote_${quoteId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  // Knowledge base chat
  knowledgeChat: async (query) => {
    const res = await fetch(`${API_BASE}/knowledge/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    return handleResponse(res);
  },

  // Upload document to knowledge base
  uploadDocument: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/knowledge/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(res);
  },

  // Knowledge base status
  knowledgeStatus: async () => {
    const res = await fetch(`${API_BASE}/knowledge/status`);
    return handleResponse(res);
  },

  // Get all quotes
  getQuotes: async () => {
    const res = await fetch(`${API_BASE}/quotes`);
    return handleResponse(res);
  },

  // Get single quote
  getQuote: async (quoteId) => {
    const res = await fetch(`${API_BASE}/quotes/${quoteId}`);
    return handleResponse(res);
  },

  // What-if simulation
  simulate: async (basePrice, cost, competitorPrice, adjustments = null) => {
    const res = await fetch(`${API_BASE}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        base_price: basePrice,
        cost: cost,
        competitor_price: competitorPrice,
        adjustments: adjustments || [-15, -10, -5, 0, 5, 10, 15],
      }),
    });
    return handleResponse(res);
  },

  // List products
  getProducts: async () => {
    const res = await fetch(`${API_BASE}/products`);
    return handleResponse(res);
  },

  // Countries + tax rates
  getCountries: async () => {
    const res = await fetch(`${API_BASE}/countries`);
    return handleResponse(res);
  },

  getTaxRate: async (country, product) => {
    const params = new URLSearchParams({ country });
    if (product) params.append("product", product);
    const res = await fetch(`${API_BASE}/tax-rate?${params}`);
    return handleResponse(res);
  },

  // Global sourcing analysis
  getSourcing: async (product, clientCountry, quantity, costPerUnit) => {
    const res = await fetch(`${API_BASE}/sourcing`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product,
        client_country: clientCountry,
        quantity,
        cost_per_unit: costPerUnit,
      }),
    });
    return handleResponse(res);
  },

};

