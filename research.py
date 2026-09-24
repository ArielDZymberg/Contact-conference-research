"""Pesquisa de pessoas e fundos/empresas usando Claude com busca na web."""

import json
import os
from datetime import date

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_CONTINUATIONS = 5

NOT_FOUND = "Não encontrado"

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


class ResearchError(Exception):
    pass


RESEARCH_SYSTEM = """Você é um analista de pesquisa que prepara briefings curtos sobre pessoas que um \
profissional do mercado financeiro vai encontrar em uma conferência.

Pesquise na web (priorize o perfil público do LinkedIn da pessoa; depois o site oficial do fundo/empresa, \
reguladores como SEC/CVM/FCA, relatórios, notícias e bases como Bloomberg, Morningstar, PitchBook, Crunchbase, \
Preqin, sites de conferências). Confirme que a pessoa encontrada é de fato a pessoa do fundo/empresa informado; \
se houver homônimos, diga isso explicitamente.

Levante:
1. Pessoa: cargo atual, trajetória relevante (empregos anteriores, formação), área de atuação e URL do LinkedIn.
2. Fundo/empresa: o que faz, tipo (gestora, hedge fund, family office, fundo de pensão, banco, empresa \
operacional etc.), sede, ano de fundação, principais produtos/fundos.
3. Se a pessoa for portfolio manager, CIO, analista, alocador ou o cargo/empresa fizer sentido: a estratégia \
de investimento (long-only, long-short, multi-strategy, macro, crédito, quant, event-driven, private equity, \
venture capital etc.), classes de ativos, regiões e setores de foco.
4. AUM mais recente do fundo/empresa, com a data de referência e a fonte (ex.: Form ADV, site oficial, \
notícias). Se houver AUM da estratégia/fundo específico da pessoa, traga também.
5. Outras informações financeiras relevantes e que façam sentido para o tipo de instituição (ex.: \
performance/retornos divulgados, número de funcionários, receita, valuation, rodadas de captação, rating, \
capital sob consultoria, número de fundos, principais investidores, captações recentes).

Seja factual. Não invente números: se não achar algo em fonte confiável, diga explicitamente que não foi \
encontrado. Informe a data de referência de cada número. Escreva as anotações finais em português."""


STRUCTURE_SYSTEM = """Você converte anotações de pesquisa em um briefing estruturado em português (Brasil). \
Use apenas informações presentes nas anotações. Quando algo não tiver sido encontrado, use exatamente o texto \
"Não encontrado" no campo correspondente e liste o item em "nao_encontrado". Os resumos devem ter 2-3 linhas \
(no máximo ~60 palavras cada)."""


_TEXT = {"type": "string"}

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "pessoa": {
            "type": "object",
            "properties": {
                "nome": _TEXT,
                "cargo": _TEXT,
                "linkedin_url": {"type": "string", "description": "URL do LinkedIn ou 'Não encontrado'"},
                "resumo": {"type": "string", "description": "Resumo de 2-3 linhas sobre a pessoa"},
            },
            "required": ["nome", "cargo", "linkedin_url", "resumo"],
            "additionalProperties": False,
        },
        "empresa": {
            "type": "object",
            "properties": {
                "nome": _TEXT,
                "tipo": {"type": "string", "description": "Ex.: gestora, hedge fund, family office, empresa"},
                "sede": _TEXT,
                "site": _TEXT,
                "resumo": {"type": "string", "description": "Resumo de 2-3 linhas sobre o fundo/empresa"},
            },
            "required": ["nome", "tipo", "sede", "site", "resumo"],
            "additionalProperties": False,
        },
        "estrategia": {
            "type": "object",
            "properties": {
                "aplicavel": {
                    "type": "boolean",
                    "description": "true se a pessoa for PM/investidor ou se estratégia fizer sentido para a empresa",
                },
                "tipo": {"type": "string", "description": "Ex.: Long-only, Long-short, Macro, Crédito"},
                "descricao": {"type": "string", "description": "Classes de ativos, regiões, setores, estilo"},
            },
            "required": ["aplicavel", "tipo", "descricao"],
            "additionalProperties": False,
        },
        "aum": {
            "type": "object",
            "properties": {
                "valor": {"type": "string", "description": "Ex.: US$ 12,5 bi ou 'Não encontrado'"},
                "data_referencia": _TEXT,
                "fonte": _TEXT,
                "observacao": {"type": "string", "description": "Ex.: AUM da estratégia específica; vazio se nada"},
            },
            "required": ["valor", "data_referencia", "fonte", "observacao"],
            "additionalProperties": False,
        },
        "outras_informacoes_financeiras": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"item": _TEXT, "valor": _TEXT, "fonte": _TEXT},
                "required": ["item", "valor", "fonte"],
                "additionalProperties": False,
            },
        },
        "nao_encontrado": {
            "type": "array",
            "items": _TEXT,
            "description": "Informações que não foi possível encontrar",
        },
        "alertas": {
            "type": "array",
            "items": _TEXT,
            "description": "Ex.: homônimos, informação possivelmente desatualizada, pessoa mudou de empresa",
        },
    },
    "required": [
        "pessoa",
        "empresa",
        "estrategia",
        "aum",
        "outras_informacoes_financeiras",
        "nao_encontrado",
        "alertas",
    ],
    "additionalProperties": False,
}


def _check_refusal(response) -> None:
    if response.stop_reason == "refusal":
        raise ResearchError("O modelo recusou esta pesquisa. Tente reformular os dados informados.")


def _collect_sources(content) -> list[dict]:
    """Fontes citadas no texto; se não houver citações, usa os resultados de busca."""
    cited, searched = {}, {}
    for block in content:
        if block.type == "text":
            for c in getattr(block, "citations", None) or []:
                url = getattr(c, "url", None)
                if url and url not in cited:
                    cited[url] = getattr(c, "title", None) or url
        elif block.type == "web_search_tool_result" and isinstance(block.content, list):
            for r in block.content:
                url = getattr(r, "url", None)
                if url and url not in searched:
                    searched[url] = getattr(r, "title", None) or url
    chosen = cited or dict(list(searched.items())[:8])
    return [{"titulo": t, "url": u} for u, t in chosen.items()]


def _run_web_research(name: str, company: str, extra: str) -> tuple[str, list[dict]]:
    client = get_client()
    user_msg = f"Pessoa: {name}\nFundo/empresa: {company or 'não informado'}\nData de hoje: {date.today():%d/%m/%Y}"
    if extra:
        user_msg += f"\nContexto adicional: {extra}"
    user_msg += "\n\nFaça a pesquisa e termine com anotações completas e organizadas de tudo o que encontrou e não encontrou."

    messages = [{"role": "user", "content": user_msg}]
    tools = [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": 10},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 6},
    ]
    all_content = []
    for _ in range(MAX_CONTINUATIONS + 1):
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=32000,
            system=RESEARCH_SYSTEM,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            tools=tools,
            messages=messages,
            betas=[FALLBACK_BETA],
            fallbacks="default",
        ) as stream:
            response = stream.get_final_message()
        _check_refusal(response)
        all_content.extend(response.content)
        if response.stop_reason != "pause_turn":
            break
        # Turno pausado pelo servidor: reenviar para continuar de onde parou.
        messages = [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": response.content},
        ]

    notes = "\n".join(b.text for b in response.content if b.type == "text").strip()
    if not notes:
        raise ResearchError("A pesquisa não retornou resultados. Tente novamente.")
    return notes, _collect_sources(all_content)


def _structure(name: str, company: str, notes: str) -> dict:
    client = get_client()
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=STRUCTURE_SYSTEM,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": RESULT_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": f"Pessoa pesquisada: {name}\nFundo/empresa informado: {company or 'não informado'}\n\n"
                f"<anotacoes>\n{notes}\n</anotacoes>",
            }
        ],
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )
    _check_refusal(response)
    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise ResearchError("Não foi possível estruturar o resultado da pesquisa.")
    return json.loads(text)


def research_person(name: str, company: str = "", extra: str = "") -> dict:
    """Pesquisa uma pessoa e seu fundo/empresa e devolve o briefing estruturado."""
    name = name.strip()
    if not name:
        raise ResearchError("Informe o nome da pessoa.")
    notes, sources = _run_web_research(name, company.strip(), extra.strip())
    result = _structure(name, company.strip(), notes)
    result["fontes"] = sources
    result["consulta"] = {"nome": name, "empresa": company.strip()}
    result["pesquisado_em"] = date.today().isoformat()
    return result
