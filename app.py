"""Aplicação web local para pesquisar contatos de conferências."""

import io
import os
import re
import threading
import webbrowser
from datetime import date

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file

import agenda
import database
import pdf_export
import research

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB


def _error(message: str, status: int = 400):
    return jsonify({"erro": message}), status


def _api_error(e: anthropic.APIError):
    if isinstance(e, anthropic.AuthenticationError):
        return _error("Chave da API da Anthropic inválida ou ausente. Configure ANTHROPIC_API_KEY.", 401)
    if isinstance(e, anthropic.RateLimitError):
        return _error("Limite de requisições da API atingido. Aguarde um minuto e tente novamente.", 429)
    if isinstance(e, anthropic.APIConnectionError):
        return _error("Falha de conexão com a API da Anthropic. Verifique a internet.", 502)
    return _error(f"Erro na API da Anthropic: {e}", 502)


@app.get("/")
def index():
    return render_template("index.html", hoje=date.today().isoformat())


@app.post("/api/pesquisar")
def pesquisar():
    body = request.get_json(force=True)
    try:
        result = research.research_person(body.get("nome", ""), body.get("empresa", ""), body.get("contexto", ""))
    except research.ResearchError as e:
        return _error(str(e))
    except anthropic.APIError as e:
        return _api_error(e)
    return jsonify(result)


@app.post("/api/agenda")
def ler_agenda():
    f = request.files.get("arquivo")
    if not f or not f.filename:
        return _error("Selecione o arquivo da agenda.")
    try:
        people = agenda.extract_people(f.filename, f.read())
    except research.ResearchError as e:
        return _error(str(e))
    except anthropic.APIError as e:
        return _api_error(e)
    return jsonify({"pessoas": people})


@app.post("/api/base")
def adicionar_base():
    body = request.get_json(force=True)
    try:
        total = database.add_contact(
            body.get("resultado") or {},
            body.get("data_conversa", ""),
            body.get("conferencia", ""),
            body.get("observacoes", ""),
        )
    except database.DatabaseError as e:
        return _error(str(e))
    return jsonify({"ok": True, "total": total})


@app.get("/api/base")
def listar_base():
    return jsonify({"contatos": database.list_contacts(), "conferencias": database.conferences()})


@app.get("/api/base/download")
def baixar_base():
    if not database.DB_PATH.exists():
        return _error("A base ainda está vazia.", 404)
    return send_file(database.DB_PATH, as_attachment=True, download_name="base_contatos.xlsx")


@app.post("/api/pdf")
def gerar_pdf():
    results = request.get_json(force=True).get("resultados") or []
    if not results:
        return _error("Nada para exportar.")
    data = pdf_export.build_pdf(results)
    if len(results) == 1:
        nome = results[0].get("pessoa", {}).get("nome", "briefing")
        slug = re.sub(r"[^A-Za-z0-9]+", "_", nome).strip("_") or "briefing"
        filename = f"briefing_{slug}.pdf"
    else:
        filename = f"briefings_{date.today():%Y-%m-%d}.pdf"
    return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=True, download_name=filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("AVISO: ANTHROPIC_API_KEY não definida. Veja o README para configurar a chave da API.")
    if os.environ.get("ABRIR_NAVEGADOR", "1") == "1":
        threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    app.run(host="127.0.0.1", port=port, threaded=True)
