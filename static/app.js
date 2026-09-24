"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const NF = "Não encontrado";
const AGENDA_CONCURRENCY = 2;

// ---------- utilidades ----------
async function api(url, options = {}) {
  const res = await fetch(url, options);
  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  if (!res.ok) {
    const msg = isJson ? (await res.json()).erro : `Erro ${res.status}`;
    throw new Error(msg || `Erro ${res.status}`);
  }
  return isJson ? res.json() : res;
}

const postJson = (url, body) =>
  api(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

function lastConference() {
  try { return localStorage.getItem("ultimaConferencia") || ""; } catch { return ""; }
}
function rememberConference(name) {
  try { localStorage.setItem("ultimaConferencia", name); } catch { /* ignorado */ }
}

function toast(msg, kind = "ok") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

async function downloadPdf(results) {
  const res = await api("/api/pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resultados: results }),
  });
  const blob = await res.blob();
  const cd = res.headers.get("content-disposition") || "";
  const name = (cd.match(/filename="?([^";]+)"?/) || [])[1] || "briefing.pdf";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}

// ---------- abas ----------
$$(".tab").forEach((btn) =>
  btn.addEventListener("click", () => {
    $$(".tab").forEach((b) => b.classList.toggle("active", b === btn));
    $$(".panel").forEach((p) => p.classList.toggle("hidden", p.id !== `tab-${btn.dataset.tab}`));
    if (btn.dataset.tab === "base") loadBase();
  })
);

// ---------- modal "adicionar à base" ----------
let conferenceList = [];
async function refreshConferences() {
  try {
    conferenceList = (await api("/api/base")).conferencias;
  } catch { /* ignorado */ }
  $("#conferencias").innerHTML = conferenceList.map((c) => `<option value="${escapeHtml(c)}">`).join("");
}

function askBaseInfo(who, { showNotes = true } = {}) {
  const dialog = $("#modal-base");
  const form = $("#form-base");
  if (dialog.open) dialog.close("cancel");
  $("#modal-base-who").textContent = who;
  form.conferencia.value = lastConference();
  form.observacoes.value = "";
  form.observacoes.closest("label").classList.toggle("hidden", !showNotes);
  refreshConferences();
  return new Promise((resolve) => {
    const onClose = () => {
      dialog.removeEventListener("close", onClose);
      if (dialog.returnValue !== "ok") return resolve(null);
      const info = {
        data_conversa: form.data_conversa.value,
        conferencia: form.conferencia.value.trim(),
        observacoes: form.observacoes.value.trim(),
      };
      rememberConference(info.conferencia);
      resolve(info);
    };
    dialog.returnValue = "";
    dialog.addEventListener("close", onClose);
    dialog.showModal();
  });
}
$("#modal-cancel").addEventListener("click", () => $("#modal-base").close("cancel"));

async function saveToBase(result, info, card) {
  try {
    const r = await postJson("/api/base", { resultado: result, ...info });
    markSaved(card);
    toast(`${result.pessoa.nome} adicionado(a) à base (${r.total} contatos).`);
    return true;
  } catch (e) {
    toast(e.message, "err");
    return false;
  }
}

function markSaved(card) {
  $(".r-badge", card).classList.remove("hidden");
  $(".r-add", card).classList.add("hidden");
}

// ---------- renderização do resultado ----------
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

const isNF = (v) => !v || String(v).trim().toLowerCase() === NF.toLowerCase();
const nfSpan = (v) => (isNF(v) ? `<span class="nf">${NF}</span>` : escapeHtml(v));

function loadingCard(name, company) {
  const el = document.createElement("article");
  el.className = "card loading";
  el.innerHTML = `<div class="spinner"></div><div><strong>${escapeHtml(name)}</strong>${
    company ? " — " + escapeHtml(company) : ""
  }<br><span class="muted small">Pesquisando no LinkedIn e na internet… (pode levar 1-3 minutos)</span></div>`;
  return el;
}

function errorCard(name, message, retry) {
  const el = document.createElement("article");
  el.className = "card error";
  el.innerHTML = `<strong>${escapeHtml(name)}</strong><p>${escapeHtml(message)}</p>`;
  if (retry) {
    const b = document.createElement("button");
    b.className = "ghost";
    b.textContent = "Tentar novamente";
    b.addEventListener("click", () => retry(el));
    el.appendChild(b);
  }
  return el;
}

function renderResult(r, { onNew }) {
  const card = $("#tpl-result").content.firstElementChild.cloneNode(true);
  const p = r.pessoa, e = r.empresa, s = r.estrategia, a = r.aum;

  $(".r-nome", card).textContent = p.nome;
  $(".r-sub", card).textContent = [p.cargo, e.nome].filter((x) => !isNF(x)).join(" · ");
  $(".r-pessoa", card).textContent = p.resumo;
  const li = $(".r-linkedin", card);
  if (isNF(p.linkedin_url) || !/^https?:\/\//.test(p.linkedin_url)) {
    li.outerHTML = `LinkedIn: <span class="nf">${NF}</span>`;
  } else {
    li.href = p.linkedin_url;
    li.textContent = "Perfil no LinkedIn ↗";
  }
  $(".r-empresa", card).textContent = e.resumo;
  $(".r-empresa-meta", card).innerHTML = `Tipo: ${nfSpan(e.tipo)} · Sede: ${nfSpan(e.sede)} · Site: ${
    /^https?:\/\//.test(e.site) ? `<a href="${escapeHtml(e.site)}" target="_blank" rel="noopener">${escapeHtml(e.site)}</a>` : nfSpan(e.site)
  }`;

  if (s.aplicavel) {
    $(".r-estrategia", card).innerHTML = `<strong>${nfSpan(s.tipo)}</strong>${s.descricao && !isNF(s.descricao) ? "<br>" + escapeHtml(s.descricao) : ""}`;
  } else {
    $(".r-estrategia", card).innerHTML = `<span class="muted">Não se aplica a este perfil.</span>`;
  }

  $(".r-aum", card).innerHTML = nfSpan(a.valor);
  $(".r-aum-meta", card).innerHTML = isNF(a.valor)
    ? escapeHtml(a.observacao || "")
    : `Referência: ${nfSpan(a.data_referencia)} · Fonte: ${nfSpan(a.fonte)}${a.observacao ? "<br>" + escapeHtml(a.observacao) : ""}`;

  const fin = r.outras_informacoes_financeiras || [];
  if (fin.length) {
    $(".r-fin", card).innerHTML = fin
      .map((i) => `<li><strong>${escapeHtml(i.item)}:</strong> ${nfSpan(i.valor)} <span class="muted small">(${escapeHtml(i.fonte)})</span></li>`)
      .join("");
  } else {
    $(".r-fin-box", card).classList.add("hidden");
  }

  const nf = r.nao_encontrado || [];
  if (nf.length) $(".r-nf", card).innerHTML = nf.map((i) => `<li>${escapeHtml(i)}</li>`).join("");
  else $(".r-nf-box", card).classList.add("hidden");

  const alerts = r.alertas || [];
  $(".r-alerts", card).innerHTML = alerts.map((i) => `<div class="alert">⚠ ${escapeHtml(i)}</div>`).join("");

  const src = r.fontes || [];
  if (src.length) {
    $(".r-src", card).innerHTML = src
      .map((f) => `<li><a href="${escapeHtml(f.url)}" target="_blank" rel="noopener">${escapeHtml(f.titulo || f.url)}</a></li>`)
      .join("");
  } else {
    $(".r-src-box", card).classList.add("hidden");
  }

  $(".r-pdf", card).addEventListener("click", async (ev) => {
    ev.target.disabled = true;
    try { await downloadPdf([r]); } catch (err) { toast(err.message, "err"); }
    ev.target.disabled = false;
  });
  $(".r-add", card).addEventListener("click", async () => {
    const info = await askBaseInfo(`${p.nome} — ${e.nome}`);
    if (info) await saveToBase(r, info, card);
  });
  $(".r-new", card).addEventListener("click", onNew);
  card.result = r;
  return card;
}

// ---------- pesquisa individual ----------
const formInd = $("#form-individual");
const resultsInd = $("#results-individual");

function newIndividualSearch() {
  formInd.reset();
  resultsInd.innerHTML = "";
  $("#tab-individual").scrollIntoView({ behavior: "smooth" });
  formInd.nome.focus();
}

async function runIndividual(nome, empresa, contexto, addToBase) {
  const loader = loadingCard(nome, empresa);
  resultsInd.prepend(loader);

  // Pesquisa e pedido dos dados da conversa acontecem em paralelo.
  const researchP = postJson("/api/pesquisar", { nome, empresa, contexto }).then(
    (r) => ({ ok: true, r }),
    (err) => ({ ok: false, err })
  );
  const infoP = addToBase ? askBaseInfo(`${nome}${empresa ? " — " + empresa : ""}`) : Promise.resolve(null);

  const res = await researchP;
  if (!res.ok) {
    loader.replaceWith(errorCard(nome, res.err.message, (el) => {
      el.remove();
      runIndividual(nome, empresa, contexto, addToBase);
    }));
    return;
  }
  const card = renderResult(res.r, { onNew: newIndividualSearch });
  loader.replaceWith(card);
  const info = await infoP;
  if (info) await saveToBase(res.r, info, card);
}

formInd.addEventListener("submit", (ev) => {
  ev.preventDefault();
  const addToBase = ev.submitter?.dataset.add === "1";
  const nome = formInd.nome.value.trim();
  if (!nome) return;
  runIndividual(nome, formInd.empresa.value.trim(), formInd.contexto.value.trim(), addToBase);
});

// ---------- agenda ----------
const formAg = $("#form-agenda");
const peopleBox = $("#agenda-people");
const resultsAg = $("#results-agenda");
let agendaPeople = [];

function resetAgenda() {
  formAg.reset();
  agendaPeople = [];
  peopleBox.classList.add("hidden");
  $("#agenda-bulk").classList.add("hidden");
  resultsAg.innerHTML = "";
  $("#agenda-progress").textContent = "";
  $("#tab-agenda").scrollIntoView({ behavior: "smooth" });
}

formAg.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const btn = $("button[type=submit]", formAg);
  btn.disabled = true;
  btn.textContent = "Lendo agenda…";
  try {
    const data = await api("/api/agenda", { method: "POST", body: new FormData(formAg) });
    agendaPeople = data.pessoas;
    if (!agendaPeople.length) {
      toast("Nenhuma pessoa encontrada no arquivo.", "err");
      return;
    }
    $("tbody", peopleBox).innerHTML = agendaPeople
      .map(
        (p, i) => `<tr><td><input type="checkbox" data-i="${i}" checked></td><td>${escapeHtml(p.nome)}</td><td>${escapeHtml(
          p.empresa
        )}</td><td>${escapeHtml(p.cargo)}</td><td>${escapeHtml(p.sessao)}</td></tr>`
      )
      .join("");
    $("#check-all").checked = true;
    peopleBox.classList.remove("hidden");
  } catch (e) {
    toast(e.message, "err");
  } finally {
    btn.disabled = false;
    btn.textContent = "Ler agenda";
  }
});

$("#check-all").addEventListener("change", (ev) =>
  $$("tbody input[type=checkbox]", peopleBox).forEach((c) => (c.checked = ev.target.checked))
);

async function runAgenda(addToBase) {
  const selected = $$("tbody input[type=checkbox]:checked", peopleBox).map((c) => agendaPeople[+c.dataset.i]);
  if (!selected.length) return toast("Selecione ao menos uma pessoa.", "err");

  let info = null;
  if (addToBase) {
    info = await askBaseInfo(`${selected.length} pessoa(s) selecionada(s)`, { showNotes: false });
    if (!info) return;
  }

  const buttons = [$("#agenda-search"), $("#agenda-search-add")];
  buttons.forEach((b) => (b.disabled = true));
  $("#agenda-bulk").classList.remove("hidden");
  const progress = $("#agenda-progress");
  let done = 0;
  progress.textContent = `Pesquisando 0 de ${selected.length}…`;

  const queue = selected.map((p) => {
    const loader = loadingCard(p.nome, p.empresa);
    resultsAg.appendChild(loader);
    return { p, loader };
  });

  async function work({ p, loader }) {
    const contexto = [p.cargo, p.sessao].filter(Boolean).join("; ");
    try {
      const r = await postJson("/api/pesquisar", { nome: p.nome, empresa: p.empresa, contexto });
      const card = renderResult(r, { onNew: resetAgenda });
      loader.replaceWith(card);
      if (info) await saveToBase(r, info, card);
    } catch (e) {
      loader.replaceWith(errorCard(p.nome, e.message));
    }
    done += 1;
    progress.textContent = `Pesquisando ${done} de ${selected.length}…`;
  }

  const workers = Array.from({ length: AGENDA_CONCURRENCY }, async () => {
    while (queue.length) await work(queue.shift());
  });
  await Promise.all(workers);
  progress.textContent = `Concluído: ${done} pessoa(s) pesquisada(s).`;
  buttons.forEach((b) => (b.disabled = false));
}

$("#agenda-search").addEventListener("click", () => runAgenda(false));
$("#agenda-search-add").addEventListener("click", () => runAgenda(true));
$("#agenda-new").addEventListener("click", resetAgenda);
$("#agenda-pdf-all").addEventListener("click", async () => {
  const results = $$(".result", resultsAg).map((c) => c.result);
  if (!results.length) return toast("Nenhum resultado para exportar ainda.", "err");
  try { await downloadPdf(results); } catch (e) { toast(e.message, "err"); }
});

// ---------- base ----------
let baseRows = [];
async function loadBase() {
  try {
    baseRows = (await api("/api/base")).contatos.reverse();
  } catch (e) {
    return toast(e.message, "err");
  }
  renderBase();
}

function renderBase() {
  const q = $("#base-filter").value.trim().toLowerCase();
  const rows = baseRows.filter((r) => !q || Object.values(r).join(" ").toLowerCase().includes(q));
  const cols = ["Data da conversa", "Conferência", "Nome", "Cargo", "Fundo/Empresa", "Estratégia", "AUM", "Observações"];
  $("#base-table tbody").innerHTML = rows
    .map((r) => `<tr>${cols.map((c) => `<td>${escapeHtml(r[c])}</td>`).join("")}</tr>`)
    .join("");
  $("#base-empty").classList.toggle("hidden", baseRows.length > 0);
}
$("#base-filter").addEventListener("input", renderBase);
