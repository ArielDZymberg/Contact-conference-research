"""Geração do PDF com os briefings."""

from datetime import date
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Fontes TrueType com suporte a acentos/unicode; se nenhuma existir, usa Helvetica (latin-1).
_FONT_CANDIDATES = [
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
]

NAVY = (31, 58, 95)
GREY = (90, 90, 90)


class _PDF(FPDF):
    def __init__(self):
        super().__init__(format="A4")
        self.set_margins(18, 16, 18)
        self.set_auto_page_break(True, margin=16)
        self.font_name = "Helvetica"
        self.unicode = False
        for regular, bold in _FONT_CANDIDATES:
            if Path(regular).exists() and Path(bold).exists():
                self.add_font("Body", "", regular)
                self.add_font("Body", "B", bold)
                self.font_name, self.unicode = "Body", True
                break

    def txt(self, s) -> str:
        s = "" if s is None else str(s)
        if not self.unicode:
            s = s.replace("•", "-").replace("–", "-").replace("—", "-").replace("’", "'")
            s = s.replace("“", '"').replace("”", '"')
            s = s.encode("latin-1", "replace").decode("latin-1")
        return s

    def footer(self):
        self.set_y(-12)
        self.set_font(self.font_name, "", 8)
        self.set_text_color(*GREY)
        self.cell(0, 6, self.txt(f"Briefing gerado em {date.today():%d/%m/%Y} - página {self.page_no()}"), align="C")

    # --- blocos -------------------------------------------------------------
    def para(self, text, size=10, bold=False, color=(0, 0, 0), h=5):
        self.set_font(self.font_name, "B" if bold else "", size)
        self.set_text_color(*color)
        self.multi_cell(0, h, self.txt(text), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def section(self, title):
        self.ln(3)
        self.para(title.upper(), size=9, bold=True, color=NAVY)
        self.set_draw_color(*NAVY)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1.5)


def _add_briefing(pdf: _PDF, r: dict) -> None:
    pessoa, empresa = r.get("pessoa", {}), r.get("empresa", {})
    estrategia, aum = r.get("estrategia", {}), r.get("aum", {})

    pdf.add_page()
    pdf.para(pessoa.get("nome", ""), size=18, bold=True, color=NAVY, h=8)
    pdf.para(f"{pessoa.get('cargo', '')} - {empresa.get('nome', '')}", size=11, color=GREY, h=6)

    pdf.section("Pessoa")
    pdf.para(pessoa.get("resumo", ""))
    pdf.para(f"LinkedIn: {pessoa.get('linkedin_url', '')}", size=9, color=GREY)

    pdf.section("Fundo / Empresa")
    pdf.para(empresa.get("resumo", ""))
    pdf.para(
        f"Tipo: {empresa.get('tipo', '')}   |   Sede: {empresa.get('sede', '')}   |   Site: {empresa.get('site', '')}",
        size=9,
        color=GREY,
    )

    if estrategia.get("aplicavel"):
        pdf.section("Estratégia")
        pdf.para(estrategia.get("tipo", ""), bold=True)
        if estrategia.get("descricao"):
            pdf.para(estrategia["descricao"])

    pdf.section("AUM")
    pdf.para(aum.get("valor", ""), size=12, bold=True, h=6)
    pdf.para(f"Referência: {aum.get('data_referencia', '')}   |   Fonte: {aum.get('fonte', '')}", size=9, color=GREY)
    if aum.get("observacao"):
        pdf.para(aum["observacao"], size=9)

    infos = r.get("outras_informacoes_financeiras") or []
    if infos:
        pdf.section("Outras informações financeiras")
        for i in infos:
            pdf.para(f"- {i.get('item', '')}: {i.get('valor', '')}  ({i.get('fonte', '')})", size=9.5)

    if r.get("nao_encontrado"):
        pdf.section("Não encontrado")
        for i in r["nao_encontrado"]:
            pdf.para(f"- {i}", size=9.5)

    if r.get("alertas"):
        pdf.section("Alertas")
        for i in r["alertas"]:
            pdf.para(f"- {i}", size=9.5)

    if r.get("fontes"):
        pdf.section("Fontes")
        for f in r["fontes"][:12]:
            pdf.para(f"- {f.get('titulo', '')}: {f.get('url', '')}", size=8, color=GREY, h=4)


def build_pdf(results: list[dict]) -> bytes:
    pdf = _PDF()
    for r in results:
        _add_briefing(pdf, r)
    return bytes(pdf.output())
