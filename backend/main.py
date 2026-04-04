"""
IntelliQuote API — FastAPI Orchestrator (Production Edition)
New endpoints: /api/strategies, /api/feedback/{id}, /api/extract-pdf
"""
import os
import sys
import uuid
import json
import io
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Ensure backend directory is in Python path
BACKEND_DIR = os.path.dirname(__file__)
sys.path.insert(0, BACKEND_DIR)

from agents.rfp_parser import parse_rfp
from agents.pricing_agent import get_pricing, list_all_products
from agents.competitor_agent import get_competitor_analysis
from agents.knowledge_agent import get_knowledge_context
from agents.strategy_agent import decide_strategy, compute_strategy_variant
from agents.drafting_agent import generate_proposal_pdf
from agents.sourcing_agent import get_sourcing_options
from services.currency_service import convert_currency, convert_for_country, COUNTRY_CURRENCY
from services.tax_service import calculate_tax, get_available_regions, get_india_gst_rate
from services.feedback_service import record_feedback, get_feedback_stats, get_quote_feedback
from rag.ingestion import ingest_all_documents
from rag.embeddings import generate_embeddings
from rag.vector_store import build_index, load_index, get_index_stats
from rag.retriever import search_knowledge
from rag.conflict_detector import detect_conflicts
from rag.decision_memory import save_decision, get_memory_stats, recall_similar_cases
from models import QuoteOutput, StrategiesComparison


# ── In-memory storage ──
quotes_db: list[QuoteOutput] = []


# ── Startup / Shutdown ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting IntelliQuote...")
    if not load_index():
        print("📚 Building knowledge index from documents...")
        doc_dir = os.path.join(BACKEND_DIR, "data", "documents")
        chunks = ingest_all_documents(doc_dir)
        if chunks:
            texts = [c["text"] for c in chunks]
            embeddings = generate_embeddings(texts)
            build_index(embeddings, chunks)
    mem = get_memory_stats()
    print(f"✅ Decision memory ready: {mem['total_cases']} past cases")
    print("✅ IntelliQuote ready!")
    yield
    print("👋 Shutting down IntelliQuote")


# ── Create app ──
app = FastAPI(
    title="IntelliQuote API",
    description="Global Sourcing & Pricing Intelligence Platform — Production Edition",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated PDFs
outputs_dir = os.path.join(BACKEND_DIR, "outputs")
os.makedirs(outputs_dir, exist_ok=True)


# ══════════════════════════════════════════
# CORE: Full RFP Processing Pipeline
# ══════════════════════════════════════════
@app.post("/api/process-rfp")
async def process_rfp_full(data: dict):
    """
    Full pipeline: RFP Text → Parse → Knowledge → Price → Compete → Strategy → Output
    Body: { "text": "...", "strategy_mode": "balanced", "country_override": "USA" }
    """
    rfp_text       = data.get("text", "")
    strategy_mode  = data.get("strategy_mode", "balanced")
    country_override = data.get("country_override")  # explicit country from UI dropdown

    if not rfp_text.strip():
        raise HTTPException(status_code=400, detail="No RFP text provided")

    # AGENT 1: Parse RFP
    parsed = parse_rfp(rfp_text)

    # Apply country override from UI if provided
    if country_override and country_override.strip():
        parsed.client_country = country_override.strip()

    effective_country = parsed.client_country or "India"

    # AGENT 2 (SME01): Get Knowledge Context
    knowledge = get_knowledge_context(
        query=f"pricing policy for {parsed.product} quantity {parsed.quantity}",
        product=parsed.product,
        client=parsed.client_name or ""
    )

    # AGENT 3: Get Internal Pricing
    pricing = get_pricing(parsed.product, parsed.quantity)

    # AGENT 4: Get Competitor Analysis
    competitor = get_competitor_analysis(parsed.product)

    # AGENT 4b: Global Sourcing Analysis
    sourcing = None
    try:
        sourcing = get_sourcing_options(
            product=parsed.product,
            client_country=effective_country,
            quantity=parsed.quantity,
            baseline_cost_per_unit=pricing.cost_per_unit,
        )
    except Exception as e:
        print(f"⚠️ Sourcing engine skipped (non-critical): {e}")

    # ── Pre-compute geo data so strategy agent can use it ──
    subtotal_pre   = pricing.base_price * parsed.quantity
    tax_info_pre   = calculate_tax(subtotal_pre, effective_country, product=parsed.product)
    currency_info_pre = None
    if effective_country != "India":
        currency_info_pre = convert_for_country(tax_info_pre["total"], effective_country)

    # AGENT 5: Strategic Decision
    strategy = decide_strategy(
        pricing=pricing,
        competitor=competitor,
        knowledge=knowledge,
        quantity=parsed.quantity,
        special_requirements=parsed.special_requirements,
        strategy_mode=strategy_mode,
        client_country=effective_country,
        tax_info=tax_info_pre,
        currency_info=currency_info_pre,
        sourcing=sourcing,
    )

    # ── Final tax & currency on actual strategy price ──
    subtotal  = strategy.final_price * parsed.quantity
    tax_info  = calculate_tax(subtotal, effective_country, product=parsed.product)

    currency_info = None
    if effective_country != "India":
        currency_info = convert_for_country(tax_info["total"], effective_country)

    # ── Per-unit converted price ──
    unit_currency = None
    if effective_country != "India":
        unit_currency = convert_for_country(strategy.final_price, effective_country)

    # Create quote record
    now = datetime.now()
    quote = QuoteOutput(
        id=str(uuid.uuid4())[:8],
        created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        client_name=parsed.client_name or "Unknown Client",
        parsed_rfp=parsed,
        pricing=pricing,
        competitor=competitor,
        knowledge_context=knowledge,
        strategy=strategy,
        sourcing=sourcing,
        status="draft"
    )
    quotes_db.append(quote)

    # ── Save decision to memory ──
    try:
        save_decision(
            quote_id=quote.id,
            product=pricing.product,
            quantity=parsed.quantity,
            strategy_type=strategy.strategy_type,
            final_price=strategy.final_price,
            margin_percent=strategy.margin_percent,
            win_probability=strategy.win_probability or "N/A",
            client_country=effective_country,
            reasoning=strategy.reasoning,
        )
    except Exception as e:
        print(f"⚠️ Memory save failed (non-critical): {e}")

    return {
        "status": "success",
        "quote_id": quote.id,
        "summary": {
            "final_price":         strategy.final_price,
            "strategy":            strategy.strategy_type,
            "win_probability":     strategy.win_probability,
            "win_probability_pct": strategy.win_probability_pct,
            "risk_level":          strategy.risk_level,
            "confidence_score":    strategy.confidence_score,
            "below_cost_pivot":    strategy.below_cost_pivot,
        },
        "analysis": {
            "cost":             pricing.cost_per_unit,
            "competitor_price": competitor.competitor_price,
            "margin":           strategy.margin_percent,
            "market_avg":       competitor.market_avg,
            "market_low":       competitor.market_low,
            "market_high":      competitor.market_high,
        },
        "geo": {
            "country":          effective_country,
            "region":           strategy.geo_region,
            "currency":         tax_info.get("currency", "INR"),
            "currency_symbol":  tax_info.get("symbol", "₹"),
            "is_international": effective_country != "India",
            "tax_name":         tax_info.get("tax_name"),
            "tax_rate":         tax_info.get("tax_rate"),
            "tax_amount":       tax_info.get("tax_amount"),
            "subtotal_inr":     subtotal,
            "grand_total_inr":  tax_info.get("total"),
        },
        "currency":      currency_info,
        "unit_currency": unit_currency,
        "value_additions":      strategy.value_additions,
        "negotiation_tactics":  strategy.negotiation_tactics,
        "insights":             strategy.insights,
        "reasoning":            strategy.reasoning,
        "confidence_score":     strategy.confidence_score,
        "past_cases_used":      strategy.past_cases_used,
        "parsed_rfp":           parsed.model_dump(),
        "knowledge_context":    [k.model_dump() for k in knowledge],
        "pricing":              pricing.model_dump(),
        "competitor":           competitor.model_dump(),
        "strategy":             strategy.model_dump(),
        "tax":                  tax_info,
        "sourcing":             sourcing.model_dump() if sourcing else None,
    }


# ── Helper: countries & tax rates list ──────────────────────────────────
@app.get("/api/countries")
async def get_countries():
    """Returns all supported countries with tax and currency info"""
    return get_available_regions()


@app.get("/api/tax-rate")
async def get_tax_rate(country: str = "India", product: str = None):
    """Returns tax rate for a specific country+product combination"""
    from services.tax_service import TAX_RULES
    rule = TAX_RULES.get(country, TAX_RULES["India"])
    rate = get_india_gst_rate(product) if country == "India" and product else rule["rate"]
    return {
        "country": country,
        "tax_name": rule["name"],
        "rate": rate,
        "currency": rule["currency"],
        "symbol": rule["symbol"],
    }


# ══════════════════════════════════════════
# NEW: Multi-Strategy Comparison
# ══════════════════════════════════════════
@app.post("/api/strategies")
async def get_all_strategies(data: dict):
    """
    Returns all 3 strategy variants (aggressive/balanced/premium) for a given RFP.
    Used to power the Strategy Comparison Table on the frontend.
    Body: { "text": "...", "quote_id": "optional-existing-id" }
    """
    rfp_text = data.get("text", "")
    quote_id = data.get("quote_id")

    # If quote_id provided, use existing parsed data
    if quote_id:
        quote = next((q for q in quotes_db if q.id == quote_id), None)
        if quote:
            pricing = quote.pricing
            competitor = quote.competitor
            knowledge = quote.knowledge_context
            quantity = quote.parsed_rfp.quantity
            client_country = quote.parsed_rfp.client_country or "India"
        else:
            raise HTTPException(status_code=404, detail="Quote not found")
    elif rfp_text.strip():
        parsed = parse_rfp(rfp_text)
        pricing = get_pricing(parsed.product, parsed.quantity)
        competitor = get_competitor_analysis(parsed.product)
        knowledge = get_knowledge_context(
            query=f"pricing policy for {parsed.product}",
            product=parsed.product,
            client=""
        )
        quantity = parsed.quantity
        client_country = parsed.client_country or "India"
    else:
        raise HTTPException(status_code=400, detail="Provide RFP text or quote_id")

    # Compute all 3 variants (fast rule-based, no LLM)
    aggressive = compute_strategy_variant(pricing, competitor, knowledge, quantity, "aggressive", client_country)
    balanced = compute_strategy_variant(pricing, competitor, knowledge, quantity, "balanced", client_country)
    premium = compute_strategy_variant(pricing, competitor, knowledge, quantity, "premium", client_country)

    # Recommend: pick highest win probability that's still profitable
    variants = {"aggressive": aggressive, "balanced": balanced, "premium": premium}
    recommended = max(variants.items(), key=lambda x: x[1].win_probability_pct)[0]

    return {
        "aggressive": aggressive.model_dump(),
        "balanced": balanced.model_dump(),
        "premium": premium.model_dump(),
        "recommended": recommended,
        "cost_per_unit": pricing.cost_per_unit,
        "competitor_price": competitor.competitor_price,
        "market_avg": competitor.market_avg,
    }


# ══════════════════════════════════════════
# NEW: Standalone Sourcing Analysis
# ══════════════════════════════════════════
@app.post("/api/sourcing")
async def analyze_sourcing(data: dict):
    """
    Standalone global sourcing analysis.
    Body: { "product": "...", "client_country": "India", "quantity": 100, "cost_per_unit": 500 }
    """
    product       = data.get("product", "Generic Product")
    client_country = data.get("client_country", "India")
    quantity      = int(data.get("quantity", 1))
    cost_per_unit = float(data.get("cost_per_unit", 500))

    if cost_per_unit <= 0:
        raise HTTPException(status_code=400, detail="cost_per_unit must be positive")

    sourcing = get_sourcing_options(
        product=product,
        client_country=client_country,
        quantity=quantity,
        baseline_cost_per_unit=cost_per_unit,
    )
    return sourcing.model_dump()


# ══════════════════════════════════════════
# NEW: Outcome Feedback
# ══════════════════════════════════════════
@app.get("/api/feedback/stats")
async def feedback_stats():
    """Get overall win/loss statistics"""
    return get_feedback_stats()


@app.get("/api/feedback/{quote_id}")
async def get_feedback(quote_id: str):
    """Get feedback for a specific quote"""
    feedback = get_quote_feedback(quote_id)
    if not feedback:
        return {"quote_id": quote_id, "outcome": None}
    return feedback


@app.post("/api/feedback/{quote_id}")
async def submit_feedback(quote_id: str, data: dict):
    """
    Record win/loss outcome for a quote. Updates decision memory for learning.
    Body: { "outcome": "won"|"lost", "actual_price": float, "client_feedback": "..." }
    """
    outcome = data.get("outcome", "pending")
    actual_price = data.get("actual_price")
    client_feedback = data.get("client_feedback")

    if outcome not in ("won", "lost", "pending"):
        raise HTTPException(status_code=400, detail="outcome must be 'won', 'lost', or 'pending'")

    # Get quote context for memory enrichment
    quote = next((q for q in quotes_db if q.id == quote_id), None)
    quote_data = quote.model_dump() if quote else None

    if quote:
        quote.outcome = outcome
        quote.status = "finalized" if outcome in ("won", "lost") else quote.status

    result = record_feedback(
        quote_id=quote_id,
        outcome=outcome,
        actual_price=actual_price,
        client_feedback=client_feedback,
        quote_data=quote_data,
    )

    return {
        "status": "recorded",
        "quote_id": quote_id,
        "outcome": outcome,
        "recorded_at": result["recorded_at"],
    }


# ══════════════════════════════════════════
# NEW: PDF Text Extraction
# ══════════════════════════════════════════
@app.post("/api/extract-pdf")
async def extract_pdf_text(file: UploadFile = File(...)):
    """
    Extract text from an uploaded PDF file.
    Returns the raw text for use in RFP processing.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()

    # Try PyPDF2 first
    extracted_text = ""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        pages_text = []
        for page in reader.pages:
            pages_text.append(page.extract_text() or "")
        extracted_text = "\n".join(pages_text).strip()
    except Exception as e:
        print(f"⚠️ PyPDF2 failed: {e}")

    # Fallback: pdfminer.six
    if not extracted_text:
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract
            extracted_text = pdfminer_extract(io.BytesIO(content)).strip()
        except Exception as e:
            print(f"⚠️ pdfminer failed: {e}")

    if not extracted_text:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF. Try copy-pasting the text instead.")

    return {
        "filename": file.filename,
        "text": extracted_text,
        "char_count": len(extracted_text),
        "page_count": len(PyPDF2.PdfReader(io.BytesIO(content)).pages) if extracted_text else 0,
    }


# ══════════════════════════════════════════
# PDF Generation & Download
# ══════════════════════════════════════════
@app.post("/api/generate-pdf/{quote_id}")
async def generate_pdf(quote_id: str):
    """Generate PDF for a specific quote"""
    quote = next((q for q in quotes_db if q.id == quote_id), None)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    pdf_path = generate_proposal_pdf(quote)
    quote.pdf_path = pdf_path
    quote.status = "finalized"

    return {
        "status": "generated",
        "pdf_path": pdf_path,
        "filename": os.path.basename(pdf_path)
    }


@app.get("/api/download-pdf/{quote_id}")
async def download_pdf(quote_id: str):
    """Download generated PDF"""
    quote = next((q for q in quotes_db if q.id == quote_id), None)
    if not quote or not quote.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found. Generate it first.")

    if not os.path.exists(quote.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file missing from disk")

    return FileResponse(
        quote.pdf_path,
        media_type="application/pdf",
        filename=f"IntelliQuote_{quote.id}.pdf"
    )


# ══════════════════════════════════════════
# Knowledge Base (SME01)
# ══════════════════════════════════════════
@app.post("/api/knowledge/chat")
async def knowledge_chat(data: dict):
    """Conversational Q&A over the knowledge base"""
    query = data.get("query", "")
    if not query.strip():
        raise HTTPException(status_code=400, detail="No query provided")

    results = search_knowledge(query, top_k=3)
    conflicts = detect_conflicts(results)

    context = "\n\n".join([
        f"[Source: {r.get('source', '?')}, {r.get('section', '?')}]\n{r.get('text', '')}"
        for r in results
    ])

    from services.llm_service import call_llm

    system_prompt = """You are an AI assistant for TechFlow Industries. Answer the employee's question using 
    ONLY the provided context. Always cite which document and section your answer comes from.
    If there's a conflict between sources, mention it explicitly. Output plain text, not JSON."""

    answer = call_llm(
        system_prompt,
        f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer with source citations:",
        json_mode=False
    )

    return {
        "answer": answer if isinstance(answer, str) else str(answer),
        "sources": [
            {
                "source": r.get("source", "unknown"),
                "section": r.get("section", "unknown"),
                "score": round(r.get("score", 0), 3),
                "text_preview": r.get("text", "")[:150]
            }
            for r in results
        ],
        "conflicts": conflicts if conflicts else None
    }


@app.post("/api/knowledge/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document and re-index the knowledge base"""
    doc_dir = os.path.join(BACKEND_DIR, "data", "documents")
    os.makedirs(doc_dir, exist_ok=True)

    filepath = os.path.join(doc_dir, file.filename)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    chunks = ingest_all_documents(doc_dir)
    if chunks:
        texts = [c["text"] for c in chunks]
        embeddings = generate_embeddings(texts)
        build_index(embeddings, chunks)

    return {
        "message": f"Uploaded and indexed {file.filename}",
        "chunks_created": len(chunks),
        "filename": file.filename
    }


@app.get("/api/knowledge/status")
async def knowledge_status():
    """Get knowledge base index status"""
    return get_index_stats()


# ══════════════════════════════════════════
# Quote History
# ══════════════════════════════════════════
@app.get("/api/quotes")
async def get_quotes():
    """List all quotes"""
    return [
        {
            "id": q.id,
            "client": q.client_name,
            "product": q.parsed_rfp.product,
            "quantity": q.parsed_rfp.quantity,
            "date": q.created_at,
            "price": q.strategy.final_price,
            "total": round(q.strategy.final_price * q.parsed_rfp.quantity, 2),
            "strategy": q.strategy.strategy_type,
            "status": q.status,
            "outcome": q.outcome,
            "has_pdf": q.pdf_path is not None,
            "win_probability": q.strategy.win_probability,
            "margin": q.strategy.margin_percent,
        }
        for q in quotes_db
    ]


@app.get("/api/quotes/{quote_id}")
async def get_quote(quote_id: str):
    """Get full quote details"""
    quote = next((q for q in quotes_db if q.id == quote_id), None)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote.model_dump()


# ══════════════════════════════════════════
# What-If Simulation
# ══════════════════════════════════════════
@app.post("/api/simulate")
async def simulate_pricing(data: dict):
    """What-if analysis: how does changing price affect margin & competitiveness?"""
    base_price = data.get("base_price", 100)
    cost = data.get("cost", 80)
    competitor_price = data.get("competitor_price", 95)
    adjustments = data.get("adjustments", [-15, -10, -5, 0, 5, 10, 15])

    scenarios = []
    for adj in adjustments:
        test_price = base_price + adj
        margin = ((test_price - cost) / cost) * 100 if cost > 0 else 0

        if test_price < competitor_price * 0.9:
            win_prob = 90
        elif test_price < competitor_price:
            win_prob = 70
        elif test_price < competitor_price * 1.05:
            win_prob = 50
        elif test_price < competitor_price * 1.15:
            win_prob = 30
        else:
            win_prob = 15

        scenarios.append({
            "price": round(test_price, 2),
            "adjustment": adj,
            "margin_percent": round(margin, 1),
            "win_probability": win_prob,
            "risk": "low" if margin > 15 else "medium" if margin > 8 else "high"
        })

    return {"scenarios": scenarios}


# ══════════════════════════════════════════
# Products & Pricing Catalog
# ══════════════════════════════════════════
@app.get("/api/products")
async def get_products():
    """List all products in the catalog"""
    return {"products": list_all_products()}


# ══════════════════════════════════════════
# Health Check
# ══════════════════════════════════════════
@app.get("/api/health")
async def health():
    stats = get_index_stats()
    mem = get_memory_stats()
    fb = get_feedback_stats()
    return {
        "status": "running",
        "version": "3.0.0",
        "service": "IntelliQuote — Global Sourcing & Pricing Intelligence",
        "knowledge_chunks": stats.get("total_chunks", 0),
        "quotes_generated": len(quotes_db),
        "memory_cases": mem.get("total_cases", 0),
        "memory_strategies": mem.get("strategies_used", []),
        "win_rate": fb.get("win_rate", 0),
        "total_feedback": fb.get("total_feedback", 0),
        "sourcing_engine": "online",
    }


# ══════════════════════════════════════════
# SME02: Decision Memory Stats
# ══════════════════════════════════════════
@app.get("/api/memory-stats")
async def memory_stats():
    """Get decision memory statistics"""
    return get_memory_stats()
