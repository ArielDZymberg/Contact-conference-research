#!/usr/bin/env python3
"""Gera um PDF com um briefing por página.

Uso: python briefing_pdf.py --briefings briefings.json --saida briefing.pdf
"""

import argparse
import json
import sys
from datetime import date
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer

NAVY = colors.HexColor("#1F3A5F")
GREY = colors.HexColor("#5A5A5A")
NF = "Não encontrado"

STYLES = {
    "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=NAVY),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=11, leading=14, textColor=GREY, spaceAfter=4),
    "h": ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=NAVY, spaceBefore=9),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=13.5, alignment=TA_LEFT),
    "strong": ParagraphStyle("strong", fontName="Helvetica-Bold", fontSize=12, leading=15),
    "meta": ParagraphStyle("meta", fontName="Helvetica", fontSize=8.5, leading=11, textColor=GREY),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5, leading=12.5, leftIndent=10, bulletIndent=0),
    "src": ParagraphStyle("src", fontName="Helvetica", fontSize=7.5, leading=10, textColor=GREY, leftIndent=10, bulletIndent=0),
}


def t(s) -> str:
    """Escapa para o mini-HTML do ReportLab e remove caracteres fora do cp1252 (ex.: emojis)."""
    s = "" if s is None else str(s)
    s = s.encode("cp1252", "ignore").decode("cp1252")
    return escape(s)


def is_nf(v) -> bool:
    return not v or str(v).strip().lower() == NF.lower()


def section(story, title):
    story.append(Paragraph(t(title.upper()), STYLES["h"]))
    story.append(HRFlowable(width="100%", thickness=0.6, color=NAVY, spaceBefore=1, spaceAfter=3))


def bullets(story, items, style="bullet"):
    for i in items:
        if i:
            story.append(Paragraph(i, STYLES[style], bulletText="•"))


def briefing(story, b):
    p, e = b.get("pessoa", {}), b.get("empresa", {})
    s, a = b.get("estrategia", {}), b.get("aum", {})

    story.append(Paragraph(t(p.get("nome")), STYLES["name"]))
    sub = " · ".join(x for x in (p.get("cargo"), e.get("nome")) if not is_nf(x))
    story.append(Paragraph(t(sub), STYLES["sub"]))

    alerts = [x for x in b.get("alertas") or [] if x]
    if alerts:
        story.append(Paragraph("<b>Atenção:</b> " + t(" | ".join(alerts)), STYLES["meta"]))

    section(story, "Pessoa")
    story.append(Paragraph(t(p.get("resumo")), STYLES["body"]))
    story.append(Paragraph("LinkedIn: " + t(p.get("linkedin_url") or NF), STYLES["meta"]))

    section(story, "Fundo / empresa")
    story.append(Paragraph(t(e.get("resumo")), STYLES["body"]))
    story.append(Paragraph(
        f"Tipo: {t(e.get('tipo') or NF)} | Sede: {t(e.get('sede') or NF)} | Site: {t(e.get('site') or NF)}",
        STYLES["meta"]))

    if s.get("aplicavel"):
        section(story, "Estratégia")
        story.append(Paragraph(t(s.get("tipo")), STYLES["strong"]))
        if not is_nf(s.get("descricao")):
            story.append(Paragraph(t(s.get("descricao")), STYLES["body"]))

    section(story, "AUM")
    story.append(Paragraph(t(a.get("valor") or NF), STYLES["strong"]))
    if not is_nf(a.get("valor")):
        story.append(Paragraph(
            f"Referência: {t(a.get('data_referencia') or NF)} | Fonte: {t(a.get('fonte') or NF)}", STYLES["meta"]))
    if a.get("observacao"):
        story.append(Paragraph(t(a["observacao"]), STYLES["meta"]))

    fin = b.get("outras_informacoes_financeiras") or []
    if fin:
        section(story, "Outras informações financeiras")
        bullets(story, [
            f"<b>{t(i.get('item'))}:</b> {t(i.get('valor'))} <font color='#5A5A5A' size='8'>({t(i.get('fonte'))})</font>"
            for i in fin
        ])

    nf = [x for x in b.get("nao_encontrado") or [] if x]
    if nf:
        section(story, "Não encontrado")
        bullets(story, [t(i) for i in nf])

    src = b.get("fontes") or []
    if src:
        section(story, "Fontes")
        bullets(story, [f"{t(f.get('titulo'))}: {t(f.get('url'))}" for f in src[:10]], style="src")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawCentredString(A4[0] / 2, 9 * mm, f"Briefing gerado em {date.today():%d/%m/%Y} - página {doc.page}")
    canvas.restoreState()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--briefings", required=True)
    ap.add_argument("--saida", required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.briefings).read_text(encoding="utf-8"))
    briefings = data if isinstance(data, list) else [data]

    Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(args.saida, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=18 * mm, title="Briefings de contatos")
    story = []
    for i, b in enumerate(briefings):
        if i:
            story.append(PageBreak())
        briefing(story, b)
        story.append(Spacer(1, 4))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"PDF salvo em: {args.saida} ({len(briefings)} briefing(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
