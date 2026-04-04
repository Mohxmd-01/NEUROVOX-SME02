"""
Agent 6: Drafting Agent — Business-Grade PDF Quotation Generator v3
====================================================================
Premium PDF with:
 - Clean business typography (no verbose theory)
 - Visual bar charts for strategy comparison & market analysis
 - Sourcing comparison graph
 - Tight, executive-style layout
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, KeepTogether,
)
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Group,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus.flowables import Flowable
from models import QuoteOutput


# ── Brand Palette ──────────────────────────────────────────────────────────
NAVY      = colors.HexColor('#0f2d52')
SKY       = colors.HexColor('#0284c7')
SKY_LT    = colors.HexColor('#38bdf8')
SKY_DIM   = colors.HexColor('#e0f2fe')
GREEN     = colors.HexColor('#059669')
GREEN_DIM = colors.HexColor('#d1fae5')
AMBER     = colors.HexColor('#d97706')
AMBER_DIM = colors.HexColor('#fef3c7')
RED       = colors.HexColor('#e11d48')
RED_DIM   = colors.HexColor('#ffe4e6')
VIOLET    = colors.HexColor('#7c3aed')
GRAY_900  = colors.HexColor('#0d1b2e')
GRAY_700  = colors.HexColor('#1e3a5f')
GRAY_500  = colors.HexColor('#5a7a9e')
GRAY_200  = colors.HexColor('#dce8f4')
GRAY_100  = colors.HexColor('#f0f6ff')
GRAY_50   = colors.HexColor('#f7f9fc')
WHITE     = colors.white

PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 18 * mm
T_MARGIN = B_MARGIN = 16 * mm
USABLE_W = PAGE_W - L_MARGIN - R_MARGIN


def _risk_color(risk):
    return {'low': GREEN, 'medium': AMBER, 'high': RED}.get(risk, GRAY_500)

def _strat_color(s):
    return {
        'aggressive': RED, 'competitive': SKY,
        'balanced': SKY,   'premium': VIOLET,
        'value-based': VIOLET,
    }.get(s, SKY)


# ── Custom Flowable: Inline Bar Chart ─────────────────────────────────────
class BarChart(Flowable):
    """
    Horizontal bar chart.
    bars: list of (label, value, max_value, color, suffix)
    """
    def __init__(self, bars, bar_height=10, gap=6, label_w=90, val_w=50):
        super().__init__()
        self.bars = bars
        self.bar_height = bar_height
        self.gap = gap
        self.label_w = label_w
        self.val_w = val_w
        self._avail_w = USABLE_W
        self.height = len(bars) * (bar_height + gap)
        self.width = USABLE_W

    def draw(self):
        c = self.canv
        bar_w = float(self._avail_w) - self.label_w - self.val_w - 8
        y = self.height - self.bar_height

        for label, value, max_val, fill, suffix in self.bars:
            frac = max(0, min(value / max_val, 1)) if max_val else 0

            # track
            c.setFillColor(GRAY_200)
            c.roundRect(self.label_w, y, bar_w, self.bar_height, 3, fill=1, stroke=0)

            # fill
            c.setFillColor(fill)
            c.roundRect(self.label_w, y, bar_w * frac, self.bar_height, 3, fill=1, stroke=0)

            # label
            c.setFillColor(GRAY_700)
            c.setFont('Helvetica', 8)
            c.drawString(0, y + 2, label)

            # value
            val_text = f"{suffix}{value:,.0f}" if suffix else f"{value:,.0f}"
            c.setFont('Helvetica-Bold', 8)
            c.setFillColor(fill)
            c.drawRightString(self._avail_w, y + 2, val_text)

            y -= (self.bar_height + self.gap)


class ScoreBar(Flowable):
    """Single score bar row with pct display on right"""
    def __init__(self, label, pct, fill_color, bar_h=8):
        super().__init__()
        self.label = label
        self.pct = max(0, min(pct, 100))
        self.fill = fill_color
        self.bar_h = bar_h
        self.height = bar_h + 8
        self.width = USABLE_W

    def draw(self):
        c = self.canv
        lw = 100
        vw = 36
        bw = float(USABLE_W) - lw - vw - 6

        c.setFont('Helvetica', 8)
        c.setFillColor(GRAY_700)
        c.drawString(0, 1, self.label)

        c.setFillColor(GRAY_200)
        c.roundRect(lw, 0, bw, self.bar_h, 3, fill=1, stroke=0)

        c.setFillColor(self.fill)
        c.roundRect(lw, 0, bw * self.pct / 100, self.bar_h, 3, fill=1, stroke=0)

        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(self.fill)
        c.drawRightString(float(USABLE_W), 1, f"{self.pct:.0f}%")


def _styles():
    s = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('IQTitle', parent=s['Normal'],
            fontSize=22, textColor=WHITE, fontName='Helvetica-Bold',
            leading=26, spaceAfter=2),
        'subtitle': ParagraphStyle('IQSub', parent=s['Normal'],
            fontSize=8.5, textColor=colors.HexColor('#94a3b8'), leading=12),
        'sec': ParagraphStyle('IQSec', parent=s['Normal'],
            fontSize=11, textColor=NAVY, fontName='Helvetica-Bold',
            spaceBefore=14, spaceAfter=5, leading=14),
        'body': ParagraphStyle('IQBody', parent=s['Normal'],
            fontSize=9.5, leading=14, textColor=GRAY_700),
        'small': ParagraphStyle('IQSmall', parent=s['Normal'],
            fontSize=8, leading=11, textColor=GRAY_500),
        'bullet': ParagraphStyle('IQBullet', parent=s['Normal'],
            fontSize=9.5, leading=14, textColor=GRAY_700, leftIndent=10),
        'label': ParagraphStyle('IQLabel', parent=s['Normal'],
            fontSize=7.5, textColor=GRAY_500, fontName='Helvetica',
            leading=10, spaceAfter=1),
        'kpi': ParagraphStyle('IQKpi', parent=s['Normal'],
            fontSize=18, textColor=NAVY, fontName='Helvetica-Bold',
            leading=20, alignment=TA_CENTER),
        'kpi_label': ParagraphStyle('IQKpiLabel', parent=s['Normal'],
            fontSize=7.5, textColor=GRAY_500, fontName='Helvetica',
            leading=10, alignment=TA_CENTER),
    }


def _section(label, color=SKY):
    """Return a section heading + horizontal rule"""
    st = _styles()
    return [
        Paragraph(label.upper(), st['sec']),
        HRFlowable(width='100%', thickness=1.5, color=color, spaceAfter=6),
    ]


def _kpi_cell(label, value, sub='', color=SKY):
    st = _styles()
    return Paragraph(
        f"<font size='7' color='#5a7a9e'>{label}</font><br/>"
        f"<font size='17' color='#{color.hexval()[2:]}' fontName='Helvetica-Bold'>{value}</font>"
        + (f"<br/><font size='7' color='#94a3b8'>{sub}</font>" if sub else ""),
        ParagraphStyle('k', parent=st['body'], alignment=TA_CENTER, leading=20)
    )


def generate_proposal_pdf(quote: QuoteOutput) -> str:
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"quote_{quote.id}.pdf")

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=T_MARGIN, bottomMargin=B_MARGIN,
        leftMargin=L_MARGIN, rightMargin=R_MARGIN,
    )

    st = _styles()
    el = []
    W = USABLE_W

    # ══════════════════════════════════════════
    # 1. HEADER BANNER
    # ══════════════════════════════════════════
    hdr = Table([[
        Paragraph("TECHFLOW INDUSTRIES", st['title']),
        Paragraph(
            f"<b><font color='#38bdf8'>PRICE QUOTATION</font></b><br/>"
            f"<font size='8' color='#94a3b8'>Ref: IQ-{quote.id}  ·  {quote.created_at}</font>",
            ParagraphStyle('hr', parent=st['body'], alignment=TA_RIGHT, textColor=WHITE, leading=14)
        ),
    ]], colWidths=[W * 0.6, W * 0.4])
    hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (0,-1), 16),
        ('RIGHTPADDING', (-1,0), (-1,-1), 16),
        ('ROUNDEDCORNERS', [4,4,0,0]),
    ]))
    el.append(hdr)
    el.append(Spacer(1, 2))

    # sky accent bar
    accent = Table([['']], colWidths=[W])
    accent.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), SKY),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    el.append(accent)
    el.append(Spacer(1, 10))

    # ══════════════════════════════════════════
    # 2. KPI STRIP
    # ══════════════════════════════════════════
    strat = quote.strategy
    cost  = quote.pricing.cost_per_unit

    def hex_no_hash(c): return c.hexval()[2:]

    kpi_data = [[
        _kpi_cell('RECOMMENDED PRICE', f"₹{strat.final_price:,.0f}", 'per unit', SKY),
        _kpi_cell('STRATEGY',          strat.strategy_type.title(), '', _strat_color(strat.strategy_type)),
        _kpi_cell('WIN PROBABILITY',   strat.win_probability or 'N/A', '', GREEN),
        _kpi_cell('MARGIN',            f"{strat.margin_percent}%", '', AMBER),
        _kpi_cell('RISK LEVEL',        strat.risk_level.title(), '', _risk_color(strat.risk_level)),
    ]]
    kpi_table = Table(kpi_data, colWidths=[W/5]*5)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GRAY_50),
        ('BOX', (0,0), (-1,-1), 1, GRAY_200),
        ('INNERGRID', (0,0), (-1,-1), 0.5, GRAY_200),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    el.append(kpi_table)
    el.append(Spacer(1, 14))

    # ══════════════════════════════════════════
    # 3. CLIENT & REQUIREMENTS
    # ══════════════════════════════════════════
    el += _section("Client & Order Details")
    req_rows = [
        ['CLIENT',    quote.client_name],
        ['PRODUCT',   quote.parsed_rfp.product],
        ['QUANTITY',  f"{quote.parsed_rfp.quantity:,} units"],
        ['DEADLINE',  quote.parsed_rfp.deadline],
        ['MARKET',    quote.parsed_rfp.client_country or 'India'],
    ]
    if quote.parsed_rfp.budget_hint:
        req_rows.append(['BUDGET HINT', quote.parsed_rfp.budget_hint])
    if quote.parsed_rfp.special_requirements:
        req_rows.append(['REQUIREMENTS', '  ·  '.join(quote.parsed_rfp.special_requirements)])

    req_t = Table(req_rows, colWidths=[W*0.22, W*0.78])
    req_t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), GRAY_500),
        ('TEXTCOLOR', (1,0), (1,-1), GRAY_900),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, GRAY_50]),
        ('GRID', (0,0), (-1,-1), 0.4, GRAY_200),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    el.append(req_t)
    el.append(Spacer(1, 14))

    # ══════════════════════════════════════════
    # 4. PRICING BREAKDOWN
    # ══════════════════════════════════════════
    el += _section("Pricing Breakdown")
    qty     = quote.parsed_rfp.quantity
    total   = strat.final_price * qty
    is_intl = (quote.parsed_rfp.client_country or 'India') != 'India'
    tax_lbl = 'Customs/VAT' if is_intl else 'GST (18%)'
    tax_rt  = 10 if is_intl else 18
    tax_amt = total * tax_rt / 100
    grand   = total + tax_amt

    price_rows = [
        ['DESCRIPTION',           'QTY',      'UNIT PRICE',                'AMOUNT'],
        [quote.parsed_rfp.product, f"{qty:,}", f"₹{strat.final_price:,.2f}", f"₹{total:,.2f}"],
        ['',                       '',         'Subtotal',                  f"₹{total:,.2f}"],
        ['',                       '',         tax_lbl,                     f"₹{tax_amt:,.2f}"],
        ['',                       '',         'GRAND TOTAL',               f"₹{grand:,.2f}"],
    ]
    price_t = Table(price_rows, colWidths=[W*0.40, W*0.14, W*0.24, W*0.22])
    price_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (2,2), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9.5),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, GRAY_50]),
        ('GRID', (0,0), (-1,-2), 0.4, GRAY_200),
        ('BACKGROUND', (0,-1), (-1,-1), SKY_DIM),
        ('TEXTCOLOR', (2,-1), (-1,-1), SKY),
        ('LINEABOVE', (0,-1), (-1,-1), 2, SKY),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    el.append(price_t)
    el.append(Spacer(1, 14))

    # ══════════════════════════════════════════
    # 5. STRATEGY COMPARISON — BAR CHART
    # ══════════════════════════════════════════
    if strat.alternative_prices:
        el += _section("Strategy Comparison")

        # Build bar data
        strategies = {}
        strategies[strat.strategy_type] = strat.final_price
        for k, v in strat.alternative_prices.items():
            if k != strat.strategy_type:
                strategies[k] = v

        all_prices = list(strategies.values())
        max_p = max(all_prices) * 1.1 if all_prices else 1

        COLORS_MAP = {
            'aggressive': RED, 'competitive': SKY,
            'balanced': SKY,   'premium': VIOLET,
            'value-based': VIOLET,
        }

        bar_rows = []
        for mode, price in strategies.items():
            col = COLORS_MAP.get(mode, SKY)
            label = f"{'★ ' if mode==strat.strategy_type else ''}{mode.title()}"
            bar_rows.append((label, price, max_p, col, '₹'))

        el.append(BarChart(bar_rows, bar_height=14, gap=8, label_w=100, val_w=70))
        el.append(Spacer(1, 4))

        # Table summary beneath chart
        comp_header = ['Strategy', 'Unit Price', 'Margin', 'vs Internal Cost']
        comp_rows = [comp_header]
        for mode, price in strategies.items():
            margin = round(((price - cost) / cost) * 100, 1) if cost > 0 else 0
            vs_cost = f"+{round((price-cost),0):,.0f}" if price >= cost else f"{round((price-cost),0):,.0f}"
            comp_rows.append([
                ('★ '+mode.title() if mode==strat.strategy_type else mode.title()),
                f"₹{price:,.2f}", f"{margin}%", f"₹{vs_cost}",
            ])

        comp_t = Table(comp_rows, colWidths=[W*0.28, W*0.24, W*0.20, W*0.28])
        comp_t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), GRAY_700),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [SKY_DIM, WHITE]),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.4, GRAY_200),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        el.append(Spacer(1, 6))
        el.append(comp_t)
        el.append(Spacer(1, 14))

    # ══════════════════════════════════════════
    # 6. MARKET PRICE COMPARISON — VISUAL
    # ══════════════════════════════════════════
    comp_data = quote.competitor
    el += _section("Market Price Analysis")

    mkt_bars = [
        ('Market Low',    comp_data.market_low,         comp_data.market_high * 1.05, RED,    '₹'),
        ('Our Price',     strat.final_price,             comp_data.market_high * 1.05, SKY,    '₹'),
        ('Market Average',comp_data.market_avg,          comp_data.market_high * 1.05, AMBER,  '₹'),
        ('Competitor',    comp_data.competitor_price,    comp_data.market_high * 1.05, VIOLET, '₹'),
        ('Market High',   comp_data.market_high,         comp_data.market_high * 1.05, GREEN,  '₹'),
        ('Our Cost',      cost,                          comp_data.market_high * 1.05, GRAY_500,'₹'),
    ]
    el.append(BarChart(mkt_bars, bar_height=12, gap=7, label_w=110, val_w=70))
    el.append(Spacer(1, 14))

    # ══════════════════════════════════════════
    # 7. GLOBAL SOURCING COMPARISON (if available)
    # ══════════════════════════════════════════
    if quote.sourcing:
        src = quote.sourcing
        el += _section("Global Sourcing Analysis", color=GREEN)

        # KPI row
        src_kpis = [[
            _kpi_cell('RECOMMENDED SOURCE', src.recommended.country, src.recommended.option_type.replace('_',' ').title(), SKY),
            _kpi_cell('LANDED COST', f"₹{src.recommended.total_landed_cost:,.0f}", '/unit', GREEN if src.savings_per_unit>0 else RED),
            _kpi_cell('SAVINGS/UNIT', f"₹{abs(src.savings_per_unit):,.0f}", 'vs baseline', GREEN if src.savings_per_unit>=0 else RED),
            _kpi_cell('COST IMPACT', f"{abs(src.cost_impact_percent):.1f}%", 'change', GREEN if src.cost_impact_percent<=0 else AMBER),
            _kpi_cell('DELIVERY', f"{src.recommended.delivery_days}d", 'lead time', SKY),
        ]]
        src_kpi_t = Table(src_kpis, colWidths=[W/5]*5)
        src_kpi_t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), GREEN_DIM),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bbf7d0')),
            ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor('#bbf7d0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        el.append(src_kpi_t)
        el.append(Spacer(1, 8))

        # Sourcing score bars
        all_opts = [src.recommended] + list(src.alternatives)
        if all_opts:
            el.append(Paragraph("Weighted Score Comparison (100-point scale)", st['label']))
            el.append(Spacer(1, 4))
            src_bar_data = []
            for opt in all_opts:
                marker = '★ ' if opt.country == src.recommended.country else ''
                src_bar_data.append((
                    f"{marker}{opt.region_label}",
                    opt.weighted_score, 100,
                    GREEN if opt.country == src.recommended.country else GRAY_500,
                    ''
                ))
            el.append(BarChart(src_bar_data, bar_height=12, gap=7, label_w=140, val_w=40))
            el.append(Spacer(1, 8))

        # Sourcing detail table
        src_header = ['Source', 'Country', 'Unit Cost', 'Logistics', 'Duty', 'Landed Cost', 'Delivery', 'Score']
        src_rows = [src_header]
        for opt in all_opts:
            is_rec = opt.country == src.recommended.country
            src_rows.append([
                ('★ ' if is_rec else '') + opt.option_type.replace('_',' ').title(),
                opt.country,
                f"₹{opt.cost_per_unit:,.0f}",
                f"₹{opt.logistics_cost:,.0f}",
                f"{opt.tax_rate}%",
                f"₹{opt.total_landed_cost:,.0f}",
                f"{opt.delivery_days}d",
                f"{opt.weighted_score:.0f}",
            ])
        src_t = Table(src_rows, colWidths=[W*0.16, W*0.10, W*0.11, W*0.10, W*0.08, W*0.14, W*0.10, W*0.09])  # noqa
        src_t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [GREEN_DIM, WHITE]),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.4, GRAY_200),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
        ]))
        el.append(src_t)
        el.append(Spacer(1, 14))

    # ══════════════════════════════════════════
    # 8. VALUE ADDITIONS (compact chips)
    # ══════════════════════════════════════════
    if strat.value_additions:
        el += _section("Included Value Additions", color=GREEN)
        va_rows = []
        row = []
        for i, va in enumerate(strat.value_additions):
            row.append(Paragraph(f"✓  {va}", st['bullet']))
            if len(row) == 2:
                va_rows.append(row)
                row = []
        if row:
            row += [''] * (2 - len(row))
            va_rows.append(row)
        va_t = Table(va_rows, colWidths=[W*0.5, W*0.5])
        va_t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), GREEN_DIM),
            ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#bbf7d0')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        el.append(va_t)
        el.append(Spacer(1, 14))

    # ══════════════════════════════════════════
    # 9. AI DECISION CONFIDENCE
    # ══════════════════════════════════════════
    el += _section("AI Decision Summary")

    conf_pct = round((strat.confidence_score or 0) * 100)
    conf_color = GREEN if conf_pct >= 70 else (AMBER if conf_pct >= 40 else RED)

    # Confidence + past cases in one row
    ai_kpi = [[
        _kpi_cell('AI CONFIDENCE', f"{conf_pct}%", '', conf_color),
        _kpi_cell('PAST CASES USED', str(strat.past_cases_used), 'from memory', SKY),
        _kpi_cell('BELOW-COST PIVOT', 'YES' if strat.below_cost_pivot else 'NO', '', RED if strat.below_cost_pivot else GREEN),
        _kpi_cell('GEO REGION', strat.geo_region or 'Domestic', strat.geo_currency or 'INR', VIOLET),
    ]]
    ai_t = Table(ai_kpi, colWidths=[W/4]*4)
    ai_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GRAY_50),
        ('BOX', (0,0), (-1,-1), 1, GRAY_200),
        ('INNERGRID', (0,0), (-1,-1), 0.5, GRAY_200),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    el.append(ai_t)
    el.append(Spacer(1, 8))

    # Confidence score bar
    el.append(ScoreBar('AI Confidence Score', conf_pct, conf_color))
    el.append(Spacer(1, 4))

    # Key insights (bullets, max 4)
    if strat.insights:
        for ins in strat.insights[:4]:
            el.append(Paragraph(f"•  {ins}", st['bullet']))
    el.append(Spacer(1, 14))

    # ══════════════════════════════════════════
    # 10. TERMS & CONDITIONS (compact)
    # ══════════════════════════════════════════
    el += _section("Terms & Conditions", color=GRAY_500)
    terms = [
        "Payment: 50% advance, balance on delivery",
        "Validity: This quotation is valid for 15 days from issue date",
        "Delivery: As per deadline specified above",
        "Warranty: Standard manufacturer warranty applies",
        "Taxes: All applicable taxes per prevailing government regulations",
        "Availability: Subject to stock at time of order confirmation",
    ]
    # Two-column terms
    mid = len(terms) // 2 + len(terms) % 2
    col1 = [Paragraph(f"• {t}", st['bullet']) for t in terms[:mid]]
    col2 = [Paragraph(f"• {t}", st['bullet']) for t in terms[mid:]]
    while len(col2) < len(col1):
        col2.append(Paragraph('', st['bullet']))
    terms_t = Table(
        [[c1, c2] for c1, c2 in zip(col1, col2)],
        colWidths=[W * 0.5, W * 0.5]
    )
    terms_t.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, GRAY_50]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.4, GRAY_200),
    ]))
    el.append(terms_t)
    el.append(Spacer(1, 16))

    # ══════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════
    el.append(HRFlowable(width='100%', thickness=0.5, color=GRAY_200))
    el.append(Spacer(1, 5))
    footer_t = Table([[
        Paragraph(
            f"Generated by <b>IntelliQuote v3.0</b> · TechFlow Industries · {quote.created_at}",
            st['small']
        ),
        Paragraph(
            "sales@techflow.in  |  +91-20-1234-5678  |  www.techflow.in",
            ParagraphStyle('fr', parent=st['small'], alignment=TA_RIGHT)
        ),
    ]], colWidths=[W * 0.55, W * 0.45])
    footer_t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    el.append(footer_t)

    doc.build(el)
    return filepath
