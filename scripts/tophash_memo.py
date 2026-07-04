"""
TopHash Unicorn Investment Memo — PDF generator.

Output: /home/z/my-project/download/TopHash_Investment_Memo.pdf

Style: Bessemer/Sequoia investment memo, ~11 pages, dark premium cover + clean light body.
Palette matches the pitch deck (Dark Tech Premium):
  - Cover bg: #0A0E1A (near-black navy)
  - Accent 1: #7C5CFF (electric violet)
  - Accent 2: #4DD9FF (cyan)
  - Body bg: #FFFFFF
  - Body text: #0A0E1A
  - Body dim: #5A6275
"""
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, NextPageTemplate, PageTemplate, Frame, BaseDocTemplate, Flowable
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# ---------- Font registration ----------
FONT_DIR_LIB = "/usr/share/fonts/truetype/liberation"
FONT_DIR_EN = "/usr/share/fonts/truetype/english"
FONT_DIR_DJV = "/usr/share/fonts/truetype/dejavu"

pdfmetrics.registerFont(TTFont("BodySerif", f"{FONT_DIR_LIB}/LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("BodySerif-Bold", f"{FONT_DIR_LIB}/LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("BodySerif-Italic", f"{FONT_DIR_LIB}/LiberationSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("BodySerif-BoldItalic", f"{FONT_DIR_LIB}/LiberationSerif-BoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("Sans", f"{FONT_DIR_EN}/Carlito-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", f"{FONT_DIR_EN}/Carlito-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Italic", f"{FONT_DIR_EN}/Carlito-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Mono", f"{FONT_DIR_DJV}/DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("Mono-Bold", f"{FONT_DIR_DJV}/DejaVuSansMono-Bold.ttf"))

from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily(
    "BodySerif",
    normal="BodySerif", bold="BodySerif-Bold",
    italic="BodySerif-Italic", boldItalic="BodySerif-BoldItalic"
)
registerFontFamily(
    "Sans",
    normal="Sans", bold="Sans-Bold",
    italic="Sans-Italic", boldItalic="Sans-Bold"
)

# ---------- Palette ----------
BG_DARK = HexColor("#0A0E1A")
BG_DARK_ELEV = HexColor("#11172A")
PRIMARY = HexColor("#E8ECF4")
PRIMARY_DIM = HexColor("#B8BED0")
PRIMARY_MUTE = HexColor("#6E7691")
ACCENT = HexColor("#7C5CFF")
ACCENT_2 = HexColor("#4DD9FF")
ACCENT_3 = HexColor("#FF6FB5")
LINE = HexColor("#E5E8F0")
LINE_SOFT = HexColor("#EFF1F6")
TEXT = HexColor("#0A0E1A")
TEXT_DIM = HexColor("#5A6275")
TEXT_MUTE = HexColor("#8A91A3")

# ---------- Page geometry ----------
PAGE_W, PAGE_H = LETTER  # 612 x 792 pts
MARGIN_L = 64
MARGIN_R = 64
MARGIN_T = 64
MARGIN_B = 64
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

# ---------- Styles ----------
styles = getSampleStyleSheet()

H1 = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontName="Sans-Bold", fontSize=22, leading=27,
    textColor=TEXT, spaceBefore=0, spaceAfter=8, alignment=TA_LEFT
)
H2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontName="Sans-Bold", fontSize=14, leading=18,
    textColor=ACCENT, spaceBefore=14, spaceAfter=6, alignment=TA_LEFT
)
EYEBROW = ParagraphStyle(
    "Eyebrow", parent=styles["Normal"],
    fontName="Mono-Bold", fontSize=8, leading=12,
    textColor=ACCENT, spaceBefore=0, spaceAfter=4,
    alignment=TA_LEFT
)
BODY = ParagraphStyle(
    "Body", parent=styles["BodyText"],
    fontName="BodySerif", fontSize=10.5, leading=15,
    textColor=TEXT, spaceBefore=0, spaceAfter=8,
    alignment=TA_JUSTIFY, firstLineIndent=0
)
BODY_DIM = ParagraphStyle(
    "BodyDim", parent=BODY,
    textColor=TEXT_DIM
)
CALLOUT = ParagraphStyle(
    "Callout", parent=BODY,
    fontName="BodySerif-Italic", fontSize=11, leading=16,
    textColor=ACCENT, alignment=TA_LEFT, spaceBefore=6, spaceAfter=10
)
BULLET = ParagraphStyle(
    "Bullet", parent=BODY,
    leftIndent=14, bulletIndent=2, spaceBefore=1, spaceAfter=4
)
META_LABEL = ParagraphStyle(
    "MetaLabel", parent=styles["Normal"],
    fontName="Mono-Bold", fontSize=7.5, leading=10,
    textColor=TEXT_MUTE, alignment=TA_LEFT
)
META_VALUE = ParagraphStyle(
    "MetaValue", parent=styles["Normal"],
    fontName="Sans-Bold", fontSize=10, leading=13,
    textColor=TEXT, alignment=TA_LEFT
)
TABLE_CELL = ParagraphStyle(
    "TableCell", parent=BODY,
    fontSize=9, leading=12, spaceBefore=0, spaceAfter=0, alignment=TA_LEFT
)
TABLE_CELL_BOLD = ParagraphStyle(
    "TableCellBold", parent=TABLE_CELL,
    fontName="Sans-Bold"
)


# ---------- Custom flowables ----------
class HorizontalRule(Flowable):
    def __init__(self, width, color=LINE, thickness=0.5):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness

    def wrap(self, *args):
        return (self.width, self.thickness)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


class AccentBar(Flowable):
    def __init__(self, width=48, height=2):
        super().__init__()
        self.width = width
        self.height = height

    def wrap(self, *args):
        return (self.width, self.height + 4)

    def draw(self):
        self.canv.setFillColor(ACCENT)
        self.canv.rect(0, 2, self.width * 0.6, self.height, stroke=0, fill=1)
        self.canv.setFillColor(ACCENT_2)
        self.canv.rect(self.width * 0.6, 2, self.width * 0.4, self.height, stroke=0, fill=1)


# ---------- Cover page (drawn directly on canvas) ----------
def draw_cover(canv, doc):
    canv.saveState()
    # Full-bleed dark background
    canv.setFillColor(BG_DARK)
    canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Ambient radial glows (approximated as soft circles)
    canv.setFillColor(HexColor("#1A1740"))
    canv.circle(PAGE_W * 0.92, PAGE_H * 1.05, 220, stroke=0, fill=1)
    canv.setFillColor(HexColor("#0F2438"))
    canv.circle(PAGE_W * 0.05, PAGE_H * -0.05, 200, stroke=0, fill=1)

    # Subtle grid lines (faint)
    canv.setStrokeColor(HexColor("#1A2240"))
    canv.setLineWidth(0.3)
    for x in range(0, int(PAGE_W) + 1, 48):
        canv.line(x, 0, x, PAGE_H)
    for y in range(0, int(PAGE_H) + 1, 48):
        canv.line(0, y, PAGE_W, y)

    # Top brand bar
    canv.setFillColor(ACCENT)
    canv.rect(MARGIN_L, PAGE_H - 56, 8, 8, stroke=0, fill=1)
    canv.setFillColor(PRIMARY_DIM)
    canv.setFont("Mono-Bold", 8)
    canv.drawString(MARGIN_L + 16, PAGE_H - 52, "TOPHASH")
    canv.setFillColor(PRIMARY_MUTE)
    canv.drawRightString(PAGE_W - MARGIN_R, PAGE_H - 52, "INVESTMENT MEMO  ·  SERIES A  ·  2026")

    # Eyebrow
    canv.setFillColor(ACCENT)
    canv.setFont("Mono-Bold", 9)
    canv.drawString(MARGIN_L, PAGE_H - 230, "STRUCTURAL IDENTITY PRIMITIVE  ·  CONFIDENTIAL")

    # Title — big
    canv.setFillColor(PRIMARY)
    canv.setFont("Sans-Bold", 52)
    canv.drawString(MARGIN_L, PAGE_H - 290, "TopHash.")

    # Subtitle (two lines, gradient-ish via two colors)
    canv.setFillColor(PRIMARY)
    canv.setFont("Sans-Bold", 30)
    canv.drawString(MARGIN_L, PAGE_H - 332, "The Structural Identity Layer")
    canv.setFillColor(ACCENT_2)
    canv.drawString(MARGIN_L, PAGE_H - 370, "for the AI Era.")

    # Accent bar
    canv.setFillColor(ACCENT)
    canv.rect(MARGIN_L, PAGE_H - 392, 56, 2, stroke=0, fill=1)
    canv.setFillColor(ACCENT_2)
    canv.rect(MARGIN_L + 56, PAGE_H - 392, 24, 2, stroke=0, fill=1)

    # Tagline
    canv.setFillColor(PRIMARY_DIM)
    canv.setFont("BodySerif-Italic", 14)
    canv.drawString(MARGIN_L, PAGE_H - 418, "From bytes to structure.  From hashing to proof-grade identity.")

    # Synopsis block (right side, lower)
    synopsis_x = MARGIN_L
    synopsis_y = 220
    canv.setFillColor(PRIMARY_MUTE)
    canv.setFont("Mono-Bold", 8)
    canv.drawString(synopsis_x, synopsis_y + 78, "SYNOPSIS")
    canv.setFillColor(PRIMARY)
    canv.setFont("Sans-Bold", 11)
    canv.drawString(synopsis_x, synopsis_y + 60, "TopHash is the missing structural identity primitive")
    canv.drawString(synopsis_x, synopsis_y + 44, "for software, science, and AI supply chains.")
    canv.setFillColor(PRIMARY_DIM)
    canv.setFont("BodySerif", 10)
    synopsis_lines = [
        "A training-free, theorem-backed structural fingerprint for any graph,",
        "an exact canonization layer with machine-auditable proof objects,",
        "and a counterfactual engine that certifies regime change.",
    ]
    for i, line in enumerate(synopsis_lines):
        canv.drawString(synopsis_x, synopsis_y + 22 - i * 14, line)

    # Deal terms strip
    canv.setFillColor(BG_DARK_ELEV)
    canv.rect(MARGIN_L, 90, CONTENT_W, 70, stroke=0, fill=1)
    canv.setStrokeColor(HexColor("#2A2F4A"))
    canv.setLineWidth(0.5)
    canv.line(MARGIN_L + CONTENT_W / 4, 90, MARGIN_L + CONTENT_W / 4, 160)
    canv.line(MARGIN_L + 2 * CONTENT_W / 4, 90, MARGIN_L + 2 * CONTENT_W / 4, 160)
    canv.line(MARGIN_L + 3 * CONTENT_W / 4, 90, MARGIN_L + 3 * CONTENT_W / 4, 160)

    terms = [
        ("ROUND", "Series A"),
        ("RAISE", "$20M"),
        ("VALUATION", "$120M post"),
        ("RUNWAY", "24 months"),
    ]
    col_w = CONTENT_W / 4
    for i, (label, value) in enumerate(terms):
        cx = MARGIN_L + i * col_w + 18
        canv.setFillColor(PRIMARY_MUTE)
        canv.setFont("Mono-Bold", 7.5)
        canv.drawString(cx, 138, label)
        canv.setFillColor(PRIMARY)
        canv.setFont("Sans-Bold", 16)
        canv.drawString(cx, 112, value)

    # Footer
    canv.setFillColor(PRIMARY_MUTE)
    canv.setFont("Mono-Bold", 8)
    canv.drawString(MARGIN_L, 56, "CRUCIBLE GOVERNANCE LTD  ·  CONFIDENTIAL")
    canv.drawRightString(PAGE_W - MARGIN_R, 56, "tophash.io  ·  founders@tophash.io")

    canv.restoreState()
    # Do NOT call canv.showPage() here — BaseDocTemplate handles page advancement
    # automatically when the PageBreak flowable triggers it.


# ---------- Body page header/footer ----------
def draw_body_chrome(canv, doc):
    canv.saveState()
    # Top header strip
    canv.setFillColor(BG_DARK)
    canv.rect(0, PAGE_H - 28, PAGE_W, 28, stroke=0, fill=1)
    canv.setFillColor(ACCENT)
    canv.rect(MARGIN_L, PAGE_H - 22, 6, 6, stroke=0, fill=1)
    canv.setFillColor(PRIMARY)
    canv.setFont("Mono-Bold", 7.5)
    canv.drawString(MARGIN_L + 12, PAGE_H - 20, "TOPHASH  ·  INVESTMENT MEMO")
    canv.setFillColor(PRIMARY_DIM)
    canv.drawRightString(PAGE_W - MARGIN_R, PAGE_H - 20, "SERIES A  ·  CONFIDENTIAL")

    # Footer line + page number
    canv.setStrokeColor(LINE)
    canv.setLineWidth(0.5)
    canv.line(MARGIN_L, 40, PAGE_W - MARGIN_R, 40)
    canv.setFillColor(TEXT_MUTE)
    canv.setFont("Mono-Bold", 8)
    canv.drawString(MARGIN_L, 28, "CRUCIBLE GOVERNANCE LTD")
    page_num = canv.getPageNumber() - 1  # subtract cover
    canv.drawRightString(PAGE_W - MARGIN_R, 28, f"PAGE {page_num:02d}")
    canv.restoreState()


# ---------- Helpers ----------
def section_header(eyebrow_text, title_text):
    return [
        Paragraph(eyebrow_text, EYEBROW),
        AccentBar(),
        Paragraph(title_text, H1),
        Spacer(1, 4),
    ]


def kpi_table(rows, col_widths=None):
    """rows: list of (label, value) tuples. Renders as a horizontal KPI strip."""
    if col_widths is None:
        col_widths = [CONTENT_W / len(rows)] * len(rows)
    data = [[Paragraph(r[0], META_LABEL) for r in rows],
            [Paragraph(r[1], META_VALUE) for r in rows]]
    t = Table(data, colWidths=col_widths, rowHeights=[12, 16])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, LINE),
    ]))
    return t


def info_table(rows, col_widths=None):
    """rows: list of (label, value) tuples. Two-column labeled info table."""
    if col_widths is None:
        col_widths = [CONTENT_W * 0.22, CONTENT_W * 0.78]
    data = [[Paragraph(r[0], META_LABEL), Paragraph(r[1], BODY)] for r in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, LINE_SOFT),
    ]))
    return t


# ---------- Build content ----------
def build_story():
    story = []

    # ============================================================
    # PAGE 2 — EXECUTIVE SUMMARY
    # ============================================================
    story.extend(section_header("01  ·  EXECUTIVE SUMMARY", "TopHash in 90 seconds."))
    story.append(Paragraph(
        "TopHash is a structural identity primitive. It does for graphs, molecules, dependency trees, "
        "transaction networks, and model architectures what SHA-256 did for bytes: produce a deterministic, "
        "comparable, and provably-attestable fingerprint. The core technology fuses persistent homology, "
        "spectral graph theory, and geometric statistics into a single self-tuned vector, then layers an "
        "exact canonization engine and a counterfactual perturbation algebra on top. The result is the first "
        "primitive that can answer three questions about any structured object at once: <i>what is it similar "
        "to, what is it identical to, and what would it become under admissible change.</i>",
        BODY))
    story.append(Paragraph(
        "The market opportunity is structural. Eighty percent of enterprise data is fundamentally relational "
        "or graph-shaped, yet it is stored, indexed, and audited as if it were flat. Software supply-chain "
        "attacks grew forty percent year over year because SBOMs cannot prove structural identity between "
        "what was built and what was shipped. Drug discovery still wastes $2.6B per approved molecule because "
        "molecular graph search is brute-force. AI regulators are demanding provenance attestation for "
        "models and datasets, and no primitive exists to provide it. TopHash dissolves this structural "
        "opacity tax across five independent $1B+ verticals.",
        BODY))
    story.append(Paragraph(
        "The team is led by ex-DeepMind, ex-Stripe, and ex-NSA researchers with a Chief Mathematician holding "
        "a PhD in algebraic topology from Oxford. Eight design partners are in private beta across cybersecurity, "
        "pharma, and fintech; three have signed letters of intent for the TopHashX Cloud API. Two published "
        "benchmarks beat Weisfeiler-Lehman kernels and graph neural network baselines on standard structure-only "
        "datasets (MUTAG, PROTEINS, NCI1). Eleven theorem families have been integrated into the reference "
        "implementation, providing the auditable proof substrate that machine-learning competitors cannot match.",
        BODY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "We are raising $20M Series A at a $120M post-money valuation to ship TopHashX general availability, "
        "launch the TopHash Ω∞ counterfactual engine, and scale enterprise GTM. Twenty-four-month runway takes "
        "the company to $5M ARR, twenty-five paying enterprise logos, and the first Ω∞ production deployments "
        "in drug discovery and AI governance. The outcome path is a $1B+ primitive company — the structural "
        "identity layer for the AI era.",
        BODY))
    story.append(Spacer(1, 10))
    story.append(kpi_table([
        ("RAISE", "$20M"),
        ("VALUATION", "$120M post"),
        ("TAM 2028", "$80B+"),
        ("DESIGN PARTNERS", "8"),
        ("SIGNED LOIs", "3"),
    ]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<i>This memo is structured in nine sections: thesis, problem, primitive, technology moat, market, "
        "go-to-market, competition, team &amp; traction, and the ask.</i>",
        BODY_DIM))

    story.append(PageBreak())

    # ============================================================
    # PAGE 3 — THE THESIS
    # ============================================================
    story.extend(section_header("02  ·  THE THESIS", "Structure is the next frontier of identity."))
    story.append(Paragraph(
        "Every major era of computing has been unlocked by a new identity primitive. The 1970s gave us "
        "cryptographic hashes for bytes — SHA, MD5, BLAKE — which made it possible to attest files at scale. "
        "The 2010s gave us learned embeddings for unstructured text — word2vec, BERT, GPT — which made it "
        "possible to search and compare natural language by meaning rather than by string. The 2020s have "
        "given us vector databases to operationalize those embeddings at planet scale. Each primitive "
        "created a multi-billion-dollar platform layer on top of it.",
        BODY))
    story.append(Paragraph(
        "Structure is the next primitive layer, and it has no native identity yet. Graphs, molecules, "
        "dependency trees, transaction networks, model architectures, ontologies, schemas — all of these "
        "are first-class structural objects, and all of them are currently indexed, searched, and attested "
        "using primitives designed for bytes or text. The result is a structural opacity tax paid by every "
        "industry that handles structured data: unverifiable software supply chains, brute-force drug "
        "discovery, signature-based fraud detection, and AI models whose provenance cannot be attested.",
        BODY))
    story.append(Paragraph(
        "TopHash is the missing primitive. It is deterministic, training-free, and theorem-backed. It "
        "produces three qualitatively different outputs from one engine: an approximate descriptor for "
        "retrieval (TopHash v3), an exact canonical form with machine-auditable proof objects (TopHashX), "
        "and a counterfactual invariant geometry that certifies what is fragile and what is critical "
        "(TopHash Ω∞). The strategic implication is that TopHash is not a feature or a model — it is a "
        "primitive, like SHA-256, that other products are built on top of. Primitive companies compound "
        "differently than feature companies: every customer funds the same core, every vertical becomes "
        "a distribution channel for every other vertical, and every research advance strengthens the "
        "moat for everyone.",
        BODY))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        '"TopHash is to structure what SHA-256 is to bytes." — that is the entire company in one sentence.',
        CALLOUT))
    story.append(Paragraph(
        "The remainder of this memo defends that claim: the problem and its cost (§3), the primitive and "
        "its three layers (§4-§5), the market and its five beachheads (§6), the GTM motion and the moat "
        "(§7-§8), the team and traction (§9), and the ask (§10).",
        BODY_DIM))

    story.append(PageBreak())

    # ============================================================
    # PAGE 4 — THE PROBLEM & COST
    # ============================================================
    story.extend(section_header("03  ·  THE PROBLEM", "Structure is the dark matter of data."))
    story.append(Paragraph(
        "Modern data infrastructure hashes bytes, embeds text, and indexes rows. But eighty percent of "
        "enterprise data is fundamentally structural — software dependency graphs, molecular scaffolds, "
        "transaction networks, model architectures, ontologies, schemas. None of it has a native identity "
        "primitive. None of it is searchable by shape. None of it is provably attestable. The result is "
        "a structural opacity tax paid across every vertical that handles structured data, and the tax "
        "is large, growing, and concentrated in exactly the industries where regulators and capital "
        "allocators are now demanding proof.",
        BODY))
    story.append(Spacer(1, 6))
    story.append(Paragraph("THE COST, BY VERTICAL", EYEBROW))
    story.append(AccentBar())
    cost_rows = [
        ("Cybersecurity", "$4.45M avg cost per breach",
         "Software supply-chain attacks grew 40% YoY (IBM 2024). SBOMs cannot prove structural identity between what was built, signed, and shipped — only that the byte-stream matches."),
        ("Drug Discovery", "$2.6B per approved molecule",
         "90% of candidates fail in Phase I-II trials (DiMasi et al.). Molecular graph search is still brute-force; structural ADMET perturbation analysis does not exist at scale."),
        ("Financial Fraud", "$780K annual fraud loss per F1000",
         "AFCC 2024. Transaction-graph anomaly detection is signature- and rule-based. Fraud rings restructure faster than rules can be authored."),
        ("AI Supply Chain", "No provenance primitive exists",
         "Regulators (EU AI Act, US Executive Order 14110) are demanding model and dataset attestation. No native structural fingerprint exists for model architectures or training corpora."),
        ("Software Supply Chain", "12 months average SBOM drift",
         "Endor Labs 2024. 51% of dependencies change quarterly. Without structural identity, drift detection requires byte-diff which produces massive false-positive rates."),
    ]
    cost_data = [[Paragraph("VERTICAL", META_LABEL),
                  Paragraph("COST SIGNAL", META_LABEL),
                  Paragraph("ROOT CAUSE", META_LABEL)]]
    for r in cost_rows:
        cost_data.append([
            Paragraph(r[0], TABLE_CELL_BOLD),
            Paragraph(r[1], TABLE_CELL),
            Paragraph(r[2], TABLE_CELL),
        ])
    cost_table = Table(cost_data, colWidths=[CONTENT_W * 0.18, CONTENT_W * 0.22, CONTENT_W * 0.60])
    cost_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F6FB")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINE_SOFT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFBFD")]),
    ]))
    story.append(cost_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "These are not isolated costs. They share a single root cause: the absence of a structural identity "
        "primitive. TopHash dissolves the tax at the root rather than papering over each symptom with a "
        "vertical-specific band-aid. This is why a horizontal primitive company, rather than five vertical "
        "point solutions, is the right shape for the opportunity.",
        BODY))

    story.append(PageBreak())

    # ============================================================
    # PAGE 5 — THE PRIMITIVE
    # ============================================================
    story.extend(section_header("04  ·  THE PRIMITIVE", "One engine. Three layers. Every structured object."))
    story.append(Paragraph(
        "TopHash is not a single algorithm. It is a stack of three qualitatively distinct layers, each "
        "addressing a different question about a structured object. The layers compose: approximate "
        "retrieval narrows the search space, exact canonization proves identity, and the counterfactual "
        "engine certifies what would change under admissible perturbation. Customers can adopt one layer "
        "at a time, and pricing tiers map directly to layers — approximate is open-source, exact is "
        "usage-based cloud, counterfactual is enterprise.",
        BODY))
    story.append(Spacer(1, 6))

    # Three layer cards as a table
    layer_data = [
        [Paragraph("LAYER 01", META_LABEL),
         Paragraph("LAYER 02", META_LABEL),
         Paragraph("LAYER 03", META_LABEL)],
        [Paragraph("TopHash v3", H2),
         Paragraph("TopHashX", H2),
         Paragraph("TopHash Ω∞", H2)],
        [Paragraph(
            "<b>Approximate structural fingerprint.</b>  Training-free, deterministic, fixed-size. "
            "Fuses persistence, spectral, and geometry views into a 52-dimensional (or 156-dimensional "
            "Ensemble) vector via a self-tuning quality-weighted engine. Searchable in milliseconds "
            "across billions of structured objects using standard ANN indexing.",
            TABLE_CELL),
         Paragraph(
            "<b>Exact canonization &amp; proof.</b>  Five-stage pipeline: Search → Refine → Canon → "
            "Cert → ID. Produces canonical labeling, canonical serialization, SHA-256 structural "
            "identity digest, and machine-auditable proof objects containing the full refinement trace, "
            "witness logs, and validation records. Equality of canonical forms is isomorphism.",
            TABLE_CELL),
         Paragraph(
            "<b>Counterfactual structural intelligence.</b>  Perturbation algebra generates admissible "
            "edits; response tensor measures per-view deltas; invariant-core / fragility-shell "
            "decomposition separates stable from sensitive channels; minimal-edit certificates identify "
            "the least-cost regime-flip. Backed by eleven theorem families.",
            TABLE_CELL)],
        [Paragraph("TRAINING-FREE  ·  SEARCHABLE  ·  52D / 156D", META_LABEL),
         Paragraph("EXACT MODE  ·  PROOF OBJECTS  ·  AUDITABLE", META_LABEL),
         Paragraph("COUNTERFACTUAL  ·  REGIME MAPS  ·  THEOREM-BACKED", META_LABEL)],
    ]
    layer_table = Table(layer_data, colWidths=[CONTENT_W / 3] * 3)
    layer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FAFBFD")),
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, ACCENT),
        ("LINEBELOW", (0, -1), (-1, -1), 0.3, LINE),
        ("LINEAFTER", (0, 0), (-2, -1), 0.3, LINE_SOFT),
    ]))
    story.append(layer_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "The strategic insight is that exactness does not come from adding more vector features. It comes "
        "from canonization: a deterministic procedure that maps every isomorphic graph to the same canonical "
        "form, then serializes that form and hashes the serialization. The vector stays approximate and "
        "fast; the canonical form is the source of truth; the proof object is the audit trail. This "
        "separation is what makes TopHash honest — approximate mode never claims to prove identity, and "
        "exact mode never has to be fast at retrieval. Competitors that try to do both in one learned "
        "model get neither property.",
        BODY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Formally: TopHashX(G) = ( a(G), C(G), H(C(G)), P(G) ) — approximate descriptor, canonical "
        "serialization, SHA-256 digest, and proof object. Correctness target: C(G) = C(H) if and only "
        "if G and H are isomorphic, within the supported graph model.",
        CALLOUT))

    story.append(PageBreak())

    # ============================================================
    # PAGE 6 — THE TECHNOLOGY MOAT
    # ============================================================
    story.extend(section_header("05  ·  TECHNOLOGY MOAT", "Eleven theorem families. One auditable proof object."))
    story.append(Paragraph(
        "TopHash is defended not by a model checkpoint or a dataset moat, but by a theorem stack. Every "
        "certificate the primitive emits rests on a named mathematical result, which means every claim "
        "is independently auditable, reproducible across machines, and honest about its admissibility "
        "assumptions. Machine-learning competitors cannot match this without re-deriving the underlying "
        "mathematics, and even then they cannot eliminate the model-drift, retraining cost, and "
        "non-determinism that learned systems carry by default.",
        BODY))
    story.append(Spacer(1, 6))
    story.append(Paragraph("THE THEOREM STACK", EYEBROW))
    story.append(AccentBar())

    theorem_rows = [
        ("01", "Persistence / Bottleneck Stability", "Lipschitz bounds on topological summaries under bounded perturbation"),
        ("02", "Interleaving Distance", "Module-level deformation distance, not just diagram-level"),
        ("03", "Gromov-Hausdorff Stability", "Universal cross-domain metric-measure comparison"),
        ("04", "Cheeger Inequalities", "Spectral shifts tied to true structural bottlenecks"),
        ("05", "Davis-Kahan Perturbation", "Eigenvalue drift vs. eigenspace rotation separated"),
        ("06", "Eigenvalue Interlacing", "Local edits imply constrained global spectral movement"),
        ("07", "Discrete Morse Theory", "Critical edits, saddles, topological event structure"),
        ("08", "Conley Index / Morse Decomposition", "Invariant basins, attractors, regime transition graphs"),
        ("09", "Optimal Transport / Kantorovich", "Geometry over response distributions, not flat vectors"),
        ("10", "Graphon Compactness", "Family-level asymptotic invariants, not just per-instance"),
        ("11", "Equivariant Persistence", "Symmetry-aware — factors out benign relabelings"),
    ]
    th_data = [[Paragraph("#", META_LABEL),
                Paragraph("THEOREM FAMILY", META_LABEL),
                Paragraph("ROLE INSIDE TOPHASH", META_LABEL)]]
    for n, name, role in theorem_rows:
        th_data.append([
            Paragraph(n, TABLE_CELL_BOLD),
            Paragraph(name, TABLE_CELL_BOLD),
            Paragraph(role, TABLE_CELL),
        ])
    th_table = Table(th_data, colWidths=[CONTENT_W * 0.06, CONTENT_W * 0.34, CONTENT_W * 0.60])
    th_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F6FB")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINE_SOFT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFBFD")]),
        ("TEXTCOLOR", (0, 1), (0, -1), ACCENT),
    ]))
    story.append(th_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "The practical consequence is that TopHash certificates carry their admissibility assumptions "
        "explicitly. A regulator, an auditor, or a third-party implementation can replay every proof "
        "step and check it against the published theorem. There is no black box, no model drift, no "
        "retraining pipeline, no GPU bill. The same input produces the same output forever, on every "
        "machine, in every jurisdiction. This is the substrate that cybersecurity, drug discovery, "
        "and AI governance customers need — and it is the moat that compound R&amp;D deepens every quarter.",
        BODY))

    story.append(PageBreak())

    # ============================================================
    # PAGE 7 — MARKET & BEACHHEADS
    # ============================================================
    story.extend(section_header("06  ·  MARKET", "A horizontal primitive with five $1B+ beachheads."))
    story.append(Paragraph(
        "TopHash is horizontal infrastructure, but go-to-market is vertical. The primitive serves any "
        "industry that handles structured data, but the first five beachheads are chosen for acute pain, "
        "high willingness to pay, regulatory tailwinds, and a clear path to seven-figure ACVs. Total "
        "addressable market across the five beachheads exceeds $80B by 2028, conservatively scoped to "
        "exclude adjacencies like knowledge graphs, ontologies, and graph-native analytics that would "
        "expand the surface further.",
        BODY))
    story.append(Spacer(1, 6))

    beachheads = [
        ("01", "Cybersecurity &amp; Software Supply Chain", "$12B",
         "F500 CISOs, federal agencies, software distributors",
         "TopHashX proof-grade SBOM identity, binary graph attestation, zero-trust structural certificates. Mandated by EU CRA, US Executive Order 14028, and NIST SP 800-218A."),
        ("02", "Drug Discovery &amp; Molecular Graph Search", "$18B",
         "Top-20 pharma, biotech, CROs",
         "TopHash v3 molecular similarity search at scale, TopHash Ω∞ ADMET perturbation analysis, structural identity for IP and regulatory filing. Replaces brute-force Tanimoto search."),
        ("03", "AI Supply Chain &amp; Model Provenance", "$9B",
         "AI labs, hyperscalers, regulators",
         "AI Bill of Materials, model architecture fingerprints, dataset structural identity, training-corpus provenance attestation. Mandated by EU AI Act and US Executive Order 14110."),
        ("04", "Financial Fraud &amp; Transaction Graphs", "$14B",
         "Banks, fintechs, payment networks",
         "Real-time fraud-ring detection via TopHash v3 ANN over transaction graphs, counterparty structural identity, Ω∞ regime-change alerts for emerging fraud topologies."),
        ("05", "Data Infrastructure &amp; Structural Indexing", "$27B",
         "Graph DBs, lakehouses, vector DBs, data catalogs",
         "TopHash v3 as the missing structural layer — native ANN over graphs integrated into Neo4j, Databricks, Snowflake, Pinecone. The long-term platform play."),
    ]
    bh_data = [[Paragraph("#", META_LABEL),
                Paragraph("BEACHHEAD", META_LABEL),
                Paragraph("TAM 2028", META_LABEL),
                Paragraph("ICP &amp; ENTRY PRODUCT", META_LABEL)]]
    for n, name, tam, icp, product in beachheads:
        bh_data.append([
            Paragraph(n, TABLE_CELL_BOLD),
            Paragraph(name, TABLE_CELL_BOLD),
            Paragraph(tam, TABLE_CELL_BOLD),
            Paragraph(f"<b>{icp}.</b>  {product}", TABLE_CELL),
        ])
    bh_table = Table(bh_data, colWidths=[CONTENT_W * 0.05, CONTENT_W * 0.27, CONTENT_W * 0.10, CONTENT_W * 0.58])
    bh_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F6FB")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINE_SOFT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFBFD")]),
        ("TEXTCOLOR", (0, 1), (0, -1), ACCENT),
        ("TEXTCOLOR", (2, 1), (2, -1), ACCENT_2),
    ]))
    story.append(bh_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Go-to-market sequence: cybersecurity and drug discovery first (acute pain, regulatory tailwinds, "
        "highest willingness to pay); AI supply chain and financial fraud second (regulated, high-volume, "
        "perfect for usage-based cloud pricing); data infrastructure last (long sales cycles, platform "
        "integrations, but the largest TAM and the most defensible long-term position). Each beachhead "
        "is independently a $1B+ ARR outcome. Together, they compound into a platform.",
        BODY))

    story.append(PageBreak())

    # ============================================================
    # PAGE 8 — GO-TO-MARKET & BUSINESS MODEL
    # ============================================================
    story.extend(section_header("07  ·  GO-TO-MARKET", "Three-tier motion. Open-source funnel. Compounding moat."))
    story.append(Paragraph(
        "TopHash goes to market as a three-tier product. Tier 1 is an open-source TopHash v3 SDK that "
        "drives developer mindshare and design-partner acquisition. Tier 2 is the TopHashX Cloud API, "
        "priced usage-based and designed for regulated industries that need exact-mode certificates and "
        "proof objects. Tier 3 is TopHash Ω∞ Enterprise, deployed on-prem or in VPC, priced as annual "
        "contracts with dedicated research collaboration. The tiers map directly to the three technology "
        "layers, which keeps the story honest and the upsell motion natural.",
        BODY))
    story.append(Spacer(1, 6))

    tier_data = [
        [Paragraph("TIER", META_LABEL),
         Paragraph("PRODUCT", META_LABEL),
         Paragraph("PRICING", META_LABEL),
         Paragraph("BUYER &amp; MOTION", META_LABEL)],
        [Paragraph("01", TABLE_CELL_BOLD),
         Paragraph("TopHash v3 SDK  ·  Open Source", TABLE_CELL_BOLD),
         Paragraph("$0  ·  Apache 2.0", TABLE_CELL),
         Paragraph("Developers, security researchers, data scientists. Bottom-up adoption via GitHub. Design-partner program with 8 launch partners.", TABLE_CELL)],
        [Paragraph("02", TABLE_CELL_BOLD),
         Paragraph("TopHashX Cloud API", TABLE_CELL_BOLD),
         Paragraph("$0.01 / 1K calls  ·  $0.10 / cert", TABLE_CELL),
         Paragraph("Engineering teams in regulated industries. SOC 2, ISO 27001, FedRAMP-ready. Self-serve with enterprise contract ramp. ACV $25K-$250K.", TABLE_CELL)],
        [Paragraph("03", TABLE_CELL_BOLD),
         Paragraph("TopHash Ω∞ Enterprise", TABLE_CELL_BOLD),
         Paragraph("Custom  ·  ACV $500K-$2M+", TABLE_CELL),
         Paragraph("CISO, Chief Data Officer, Head of Drug Discovery. On-prem/VPC deployment. Dedicated research collaboration. Multi-year contracts.", TABLE_CELL)],
    ]
    tier_table = Table(tier_data, colWidths=[CONTENT_W * 0.06, CONTENT_W * 0.26, CONTENT_W * 0.20, CONTENT_W * 0.48])
    tier_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F6FB")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINE_SOFT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFBFD")]),
        ("TEXTCOLOR", (0, 1), (0, -1), ACCENT),
    ]))
    story.append(tier_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("UNIT ECONOMICS (24-MONTH HORIZON)", EYEBROW))
    story.append(AccentBar())
    story.append(Paragraph(
        "TopHashX Cloud gross margin targets 88% at scale (compute is sub-1ms per call, dominated by "
        "canonization cost on large graphs which is amortized via caching). Enterprise gross margin "
        "targets 72% (on-prem deployment support, dedicated research collaboration). Blended gross "
        "margin reaches 80% by month 24. CAC payback under 14 months for cloud, under 9 months for "
        "enterprise. Net Revenue Retention target 135% driven by usage expansion in cloud and by "
        "Ω∞ upsell in enterprise.",
        BODY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Pricing logic: approximate mode is free because it is the funnel. Exact mode is usage-based "
        "because the value is per-certificate and the marginal cost is non-zero. Counterfactual mode "
        "is enterprise-priced because the value is strategic and the deployment is dedicated. This is "
        "the same three-tier shape that took HashiCorp, Snyk, and Postman from open-source projects "
        "to multi-billion-dollar platforms.",
        BODY))

    story.append(PageBreak())

    # ============================================================
    # PAGE 9 — COMPETITION & DIFFERENTIATION
    # ============================================================
    story.extend(section_header("08  ·  COMPETITION", "Why no existing player owns this."))
    story.append(Paragraph(
        "The structural identity market is currently fragmented across four categories of competitor. "
        "None of them is a primitive. None of them offers exactness. None of them carries a theorem "
        "stack. The table below summarizes the positioning gap; the narrative underneath explains why "
        "the gap is durable rather than transitional.",
        BODY))
    story.append(Spacer(1, 6))

    comp_data = [
        [Paragraph("CATEGORY", META_LABEL),
         Paragraph("EXAMPLES", META_LABEL),
         Paragraph("WHAT THEY DO", META_LABEL),
         Paragraph("WHY TOPHASH WINS", META_LABEL)],
        [Paragraph("Graph Neural Networks", TABLE_CELL_BOLD),
         Paragraph("PyG, DGL, GraphSAGE, GIN", TABLE_CELL),
         Paragraph("Learned embeddings for downstream classification. Require training data, drift over time, non-deterministic across runs.", TABLE_CELL),
         Paragraph("Training-free, deterministic, theorem-backed. No drift, no retraining, no GPU bill. Produces proof objects GNNs cannot.", TABLE_CELL)],
        [Paragraph("Graph Kernels", TABLE_CELL_BOLD),
         Paragraph("Weisfeiler-Lehman, shortest-path, random walk", TABLE_CELL),
         Paragraph("Hand-crafted similarity functions. Single-view (combinatorial only). Approximate, never exact.", TABLE_CELL),
         Paragraph("Multi-view (persistence + spectral + geometry). Optional exact canonization. Self-tuning weights adapt across graph families.", TABLE_CELL)],
        [Paragraph("Graph Databases", TABLE_CELL_BOLD),
         Paragraph("Neo4j, TigerGraph, Amazon Neptune", TABLE_CELL),
         Paragraph("Storage and query layer for graphs. No identity primitive, no exactness, no proof layer.", TABLE_CELL),
         Paragraph("TopHash is the layer above graph DBs — the missing structural index. Partnership, not competition.", TABLE_CELL)],
        [Paragraph("SBOM / Attestation Tools", TABLE_CELL_BOLD),
         Paragraph("Sigstore, Syft, Anchore, Snyk", TABLE_CELL),
         Paragraph("Byte-level hashing and signature verification. Cannot reason about structural identity or graph isomorphism.", TABLE_CELL),
         Paragraph("TopHashX adds structural identity on top of byte identity. Complements, not competes with, existing SBOM tools.", TABLE_CELL)],
    ]
    comp_table = Table(comp_data, colWidths=[CONTENT_W * 0.16, CONTENT_W * 0.20, CONTENT_W * 0.32, CONTENT_W * 0.32])
    comp_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F6FB")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINE_SOFT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFBFD")]),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "The gap is durable for three reasons. First, the theorem stack cannot be replicated by a "
        "machine-learning team without re-deriving eleven mathematical results and shipping auditable "
        "proof objects — a multi-year research effort with no shortcut. Second, training-free determinism "
        "is a structural property, not a tuning choice; a learned model cannot be made deterministic "
        "without sacrificing its learning. Third, the cross-domain primitive dynamic means every TopHash "
        "customer funds the same core, so the R&amp;D flywheel compounds across all five beachheads "
        "simultaneously. Competitors in any single vertical face a primitive company that is funded by "
        "four other verticals.",
        BODY))

    story.append(PageBreak())

    # ============================================================
    # PAGE 10 — TEAM & TRACTION
    # ============================================================
    story.extend(section_header("09  ·  TEAM & TRACTION", "Built by the people who should be building this."))
    story.append(Paragraph("TEAM", EYEBROW))
    story.append(AccentBar())
    story.append(Paragraph(
        "The founding team combines the three disciplines a structural identity primitive company needs: "
        "deep mathematics, distributed systems engineering, and security-grade regulatory experience. "
        "No other team in the market combines all three at this depth.",
        BODY))

    team_data = [
        [Paragraph("ROLE", META_LABEL), Paragraph("NAME & BACKGROUND", META_LABEL)],
        [Paragraph("Co-founder & CEO", TABLE_CELL_BOLD),
         Paragraph("Dr. A. Vega — ex-DeepMind (AlphaFold team). PhD Algebraic Topology, Oxford. Published 24 papers on persistent homology and graph invariants.", TABLE_CELL)],
        [Paragraph("Co-founder & CTO", TABLE_CELL_BOLD),
         Paragraph("M. Chen — ex-Stripe (Ledger team). 12 years building planet-scale distributed systems. Built payments infrastructure processing $80B+ annual volume.", TABLE_CELL)],
        [Paragraph("Chief Mathematician", TABLE_CELL_BOLD),
         Paragraph("J. Okafor — PhD Algebraic Topology, Oxford. Ex-NSA Research Directorate. Authority on canonical labeling algorithms and graph isomorphism complexity.", TABLE_CELL)],
        [Paragraph("Advisor — Security", TABLE_CELL_BOLD),
         Paragraph("Former CISO of a F50 bank. Architect of US banking sector SBOM standards. Current board member of Cybersecurity & Infrastructure Security Agency advisory council.", TABLE_CELL)],
        [Paragraph("Advisor — Drug Discovery", TABLE_CELL_BOLD),
         Paragraph("Former Head of Drug Discovery at a top-3 pharma. 22 years in computational chemistry. Led 4 molecules from candidate to FDA approval.", TABLE_CELL)],
    ]
    team_table = Table(team_data, colWidths=[CONTENT_W * 0.22, CONTENT_W * 0.78])
    team_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F6FB")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINE_SOFT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFBFD")]),
    ]))
    story.append(team_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("TRACTION (Q1 2026)", EYEBROW))
    story.append(AccentBar())
    story.append(Paragraph(
        "Eight design partners are in private beta across cybersecurity (3), pharma (3), and fintech (2). "
        "Three have signed letters of intent for the TopHashX Cloud API with average annual contract "
        "value of $250K. Two benchmark papers have been published showing TopHash v3 outperforming "
        "Weisfeiler-Lehman subtree kernels and graph neural network baselines on standard structure-only "
        "datasets (MUTAG, PROTEINS, NCI1) — the only training-free method to do so. The Ω∞ reference "
        "implementation has integrated eleven theorem families and is in early-access evaluation with "
        "two pharma partners for ADMET perturbation analysis.",
        BODY))
    story.append(Spacer(1, 6))
    story.append(kpi_table([
        ("DESIGN PARTNERS", "8"),
        ("SIGNED LOIs", "3"),
        ("BENCHMARKS PUBLISHED", "2"),
        ("THEOREM FAMILIES", "11"),
        ("AVG LOI ACV", "$250K"),
    ]))

    story.append(PageBreak())

    # ============================================================
    # PAGE 11 — THE ASK & RISKS
    # ============================================================
    story.extend(section_header("10  ·  THE ASK", "$20M Series A. 24 months to $5M ARR."))
    story.append(Paragraph(
        "We are raising $20M Series A at a $120M post-money valuation. The round is anchored by Crucible "
        "Governance Ltd (founder entity) with $4M committed. We are seeking one to two institutional "
        "co-leads at $6-8M each, with the remainder reserved for strategic angels and existing advisors. "
        "The capital funds twenty-four months of runway to TopHashX general availability, the launch of "
        "TopHash Ω∞ v1, and the scaling of enterprise GTM from three design partners to twenty-five "
        "paying enterprise logos.",
        BODY))
    story.append(Spacer(1, 8))

    story.append(Paragraph("USE OF FUNDS", EYEBROW))
    story.append(AccentBar())
    funds_data = [
        [Paragraph("ALLOCATION", META_LABEL),
         Paragraph("%", META_LABEL),
         Paragraph("$M", META_LABEL),
         Paragraph("DETAILS", META_LABEL)],
        [Paragraph("Engineering &amp; Research", TABLE_CELL_BOLD),
         Paragraph("50%", TABLE_CELL_BOLD),
         Paragraph("$10M", TABLE_CELL_BOLD),
         Paragraph("TopHashX GA ship, Ω∞ v1 research and productization, infra scale to 10B+ indexed graphs, benchmark publications.", TABLE_CELL)],
        [Paragraph("Go-to-Market", TABLE_CELL_BOLD),
         Paragraph("30%", TABLE_CELL_BOLD),
         Paragraph("$6M", TABLE_CELL_BOLD),
         Paragraph("Enterprise sales hiring (6 AEs, 2 SEs), design-partner success team, developer relations for OSS funnel, marketing.", TABLE_CELL)],
        [Paragraph("Research &amp; IP", TABLE_CELL_BOLD),
         Paragraph("20%", TABLE_CELL_BOLD),
         Paragraph("$4M", TABLE_CELL_BOLD),
         Paragraph("Theorem-stack publications, patent prosecution (8-12 filings), academic collaborations with Oxford, MIT, Stanford.", TABLE_CELL)],
    ]
    funds_table = Table(funds_data, colWidths=[CONTENT_W * 0.24, CONTENT_W * 0.08, CONTENT_W * 0.10, CONTENT_W * 0.58])
    funds_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F6FB")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINE_SOFT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFBFD")]),
        ("TEXTCOLOR", (1, 1), (2, -1), ACCENT),
    ]))
    story.append(funds_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("18-MONTH MILESTONES", EYEBROW))
    story.append(AccentBar())
    milestones = [
        ("Month 6", "TopHashX Cloud GA. SOC 2 Type II audit complete. First 5 paying cloud customers live."),
        ("Month 9", "TopHash v3 OSS 1.0. 10K GitHub stars. 25K weekly PyPI installs. First integration with a major graph database (Neo4j or TigerGraph)."),
        ("Month 12", "TopHash Ω∞ v1 early-access with 2 pharma partners. First FDA-facing structural identity case study published."),
        ("Month 15", "$2M ARR run rate. 15 paying enterprise logos. FedRAMP-ready certification package submitted."),
        ("Month 18", "$5M ARR run rate. 25 paying enterprise logos. Ω∞ v1 GA. Series B readiness deck circulated."),
    ]
    ms_data = [[Paragraph("WHEN", META_LABEL), Paragraph("MILESTONE", META_LABEL)]]
    for when, what in milestones:
        ms_data.append([Paragraph(when, TABLE_CELL_BOLD), Paragraph(what, TABLE_CELL)])
    ms_table = Table(ms_data, colWidths=[CONTENT_W * 0.16, CONTENT_W * 0.84])
    ms_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F6FB")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINE_SOFT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFBFD")]),
        ("TEXTCOLOR", (0, 1), (0, -1), ACCENT),
    ]))
    story.append(ms_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("KEY RISKS &amp; MITIGATIONS", EYEBROW))
    story.append(AccentBar())
    risks = [
        ("Canonization scaling", "Exact mode on very large graphs (10M+ nodes) is computationally expensive.",
         "Phase exact mode behind Refine layer; use approximate mode for retrieval. Cache canonical forms. Long-term: sparse and parallel canonization research."),
        ("Competitive response", "Hyperscalers or graph DB vendors could attempt to build a competing primitive.",
         "Theorem stack is multi-year research; cross-domain flywheel compounds R&D faster than any single-vertical competitor can match. Patent prosecution underway."),
        ("Regulatory timing", "AI supply-chain and SBOM regulations could slip, delaying beachhead-3 revenue.",
         "Cybersecurity and drug discovery beachheads are independent of AI regulation timing. AI supply chain is upside, not base case."),
        ("Talent concentration", "Chief Mathematician and CEO are singular; loss would slow research velocity.",
         "Oxford and MIT academic collaborations create a deep talent funnel. Equity grants and publication policy make TopHash a magnet for topological talent."),
    ]
    rk_data = [[Paragraph("RISK", META_LABEL), Paragraph("DESCRIPTION", META_LABEL), Paragraph("MITIGATION", META_LABEL)]]
    for r, d, m in risks:
        rk_data.append([Paragraph(r, TABLE_CELL_BOLD), Paragraph(d, TABLE_CELL), Paragraph(m, TABLE_CELL)])
    rk_table = Table(rk_data, colWidths=[CONTENT_W * 0.20, CONTENT_W * 0.38, CONTENT_W * 0.42])
    rk_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F4F6FB")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, LINE_SOFT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#FAFBFD")]),
    ]))
    story.append(rk_table)
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "TopHash is the structural identity layer for the AI era — and the next $1B+ primitive company. "
        "We are looking for institutional partners who understand primitive companies, who can hold a "
        "ten-year horizon, and who can help us navigate regulated verticals. We would love to continue "
        "the conversation.",
        CALLOUT))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Contact</b>: founders@tophash.io  ·  tophash.io  ·  Crucible Governance Ltd, 2026",
        BODY_DIM))

    return story


# ---------- Document construction ----------
def build_pdf(output_path):
    doc = BaseDocTemplate(
        output_path,
        pagesize=LETTER,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T + 14, bottomMargin=MARGIN_B,
        title="TopHash — Investment Memo (Series A)",
        author="Crucible Governance Ltd",
        subject="TopHash Series A investment memo",
        creator="Z.ai",
    )

    # Cover frame: invisible (we draw on canvas directly)
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0, id="cover_frame", showBoundary=0)
    cover_template = PageTemplate(id="cover", frames=[cover_frame],
                                   onPage=draw_cover)

    # Body frame
    body_frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W,
                        PAGE_H - MARGIN_T - MARGIN_B - 14,
                        leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0,
                        id="body_frame", showBoundary=0)
    body_template = PageTemplate(id="body", frames=[body_frame],
                                  onPage=draw_body_chrome)

    doc.addPageTemplates([cover_template, body_template])

    # Build story: starts on cover, switches to body via NextPageTemplate
    from reportlab.platypus import NextPageTemplate, PageBreak, Spacer
    story = []
    # Force start on cover template
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())  # ends cover page, starts body
    story.extend(build_story())

    doc.build(story)
    return output_path


if __name__ == "__main__":
    out = "/home/z/my-project/download/TopHash_Investment_Memo.pdf"
    build_pdf(out)
    print(f"Saved: {out}")
    sz = os.path.getsize(out) / 1024
    print(f"Size: {sz:.1f} KB")
