"use strict";

// Static research tool. Reads model_all_groups.json and item_domains.json from the same
// folder and computes in the browser; nothing is sent anywhere and nothing is fitted here.
// Per group: logistic score over all items, then the seven group scores are normalised to sum to 1.

const MIN_ITEMS = 3;
const MAX_ITEMS = 10;
const OTHER_KEY = "Other";
const AXIS_TICKS = [0, 50, 100];
const GRID_TICKS = [25, 50, 75];
const OTHER_NOTE =
  "Other diagnoses include: personality disorders, neurocognitive disorders, dementia, and " +
  "substance- or alcohol-related diagnoses, among diagnoses that do not match the other six " +
  "groups' keywords (n = %d in the training set).";
const HINT = `<p class="hint">Select ${MIN_ITEMS} to ${MAX_ITEMS} chief problems, then press Compute.</p>`;

const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (ch) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[ch]);
const pct = (x) => (100 * x).toFixed(1) + "%";

// ---------------------------------------------------------------- model
function buildDomains(model, domainData) {
  const codeToName = new Map(model.items.map((it) => [it.code, it.name]));
  const domains = domainData.domains.map((d) => ({
    label: d.label,
    names: d.codes.map((code) => {
      if (!codeToName.has(code)) throw new Error("Unknown item code " + code);
      return codeToName.get(code);
    })
  }));
  const assigned = domains.flatMap((d) => d.names);
  if (assigned.length !== model.items.length || new Set(assigned).size !== model.items.length) {
    throw new Error("Item domains and model items differ.");
  }
  for (const c of model.classes) {
    if (model.coef[c].length !== model.items.length) throw new Error("Coefficient length differs for " + c);
  }
  return domains;
}

function probabilities(model, picked) {
  const chosen = new Set(picked);
  const x = model.items.map((it) => (chosen.has(it.name) ? 1.0 : 0.0));
  const raw = {};
  for (const c of model.classes) {
    let dot = 0.0;
    for (let i = 0; i < x.length; i++) dot += model.coef[c][i] * x[i];
    raw[c] = 1.0 / (1.0 + Math.exp(-(model.intercept[c] + dot)));
  }
  let total = 0.0;
  for (const c of model.classes) total += raw[c];
  const prob = {};
  for (const c of model.classes) prob[c] = raw[c] / total;
  return prob;
}

// Named groups by descending probability; the residual group (Other) is kept apart and never ranked.
function rankGroups(model, prob) {
  const row = (c) => {
    const cut = model.performance[c].cutoff;
    return { cls: c, label: model.labels[c], p: prob[c], cut, over: prob[c] >= cut };
  };
  const main = model.classes.filter((c) => c !== OTHER_KEY).map(row).sort((a, b) => b.p - a.p);
  const other = model.classes.includes(OTHER_KEY) ? row(OTHER_KEY) : null;
  const over = (other ? [...main, other] : main).filter((r) => r.over).sort((a, b) => b.p - a.p);
  const summary = over.length
    ? `${over.length} of ${model.classes.length} groups at or above their cut-off: ${over.map((r) => r.label).join("; ")}.`
    : "No group reaches its cut-off.";
  return { main, other, summary };
}

function selectionState(n) {
  if (n === 0) return `Select ${MIN_ITEMS} to ${MAX_ITEMS}.`;
  if (n < MIN_ITEMS) return `Select ${MIN_ITEMS - n} more (minimum ${MIN_ITEMS}).`;
  if (n > MAX_ITEMS) return `Remove ${n - MAX_ITEMS} (maximum ${MAX_ITEMS}).`;
  return "Ready to compute.";
}
const isValidCount = (n) => n >= MIN_ITEMS && n <= MAX_ITEMS;

// ---------------------------------------------------------------- rendering
function countHTML(domains, picked) {
  const chosen = new Set(picked);
  let html = `<p class="cnt"><strong>${picked.length} selected</strong> <span class="muted">&middot; ${selectionState(picked.length)}</span></p>`;
  const lines = domains.map((d) => {
    const sel = d.names.filter((n) => chosen.has(n));
    return sel.length
      ? `<li><strong>${escapeHTML(d.label)}</strong> <span class="muted">${sel.length} of ${d.names.length}</span><br>${sel.map(escapeHTML).join("; ")}</li>`
      : "";
  }).join("");
  if (lines) html += `<ul class="sel">${lines}</ul>`;
  return html;
}

function groupRowHTML(r) {
  const kind = r.over ? "above" : "below";
  const grid = GRID_TICKS.map((t) => `<i class="g" style="left:${t}%"></i>`).join("");
  return `<tr class="${kind}" role="row"><th scope="row" role="rowheader">${escapeHTML(r.label)}</th>` +
    `<td class="bar" role="cell"><div class="track" aria-hidden="true">${grid}` +
    `<div class="fill ${kind}" style="width:${(100 * Math.min(r.p, 1)).toFixed(2)}%"></div>` +
    `<div class="tick" style="left:${(100 * Math.min(r.cut, 1)).toFixed(2)}%"></div></div></td>` +
    `<td class="num p" role="cell">${pct(r.p)}</td>` +
    `<td class="num cut" role="cell" data-label="Cut-off">${pct(r.cut)}</td>` +
    `<td class="status" role="cell"><span class="mk ${kind}" aria-hidden="true"></span>${r.over ? "At or above" : "Below"}</td></tr>`;
}

function renderResult(model, selectedNames) {
  const valid = new Set(model.items.map((it) => it.name));
  const order = new Map(model.items.map((it, i) => [it.name, i]));
  const picked = [...new Set(selectedNames.filter((n) => valid.has(n)))].sort((a, b) => order.get(a) - order.get(b));
  if (!isValidCount(picked.length)) {
    return `<p class="hint">Select between ${MIN_ITEMS} and ${MAX_ITEMS} chief problems. You selected ${picked.length}.</p>`;
  }
  const { main, other, summary } = rankGroups(model, probabilities(model, picked));
  const axis = AXIS_TICKS.map((t) => `<span style="left:${t}%">${t}%</span>`).join("");
  let html = `<p class="echo"><strong>Input (${picked.length}):</strong> ${picked.map(escapeHTML).join("; ")}</p>` +
    `<p class="summary">${escapeHTML(summary)}</p>` +
    '<table class="rt" role="table"><caption class="sr">Probability of each diagnostic group with its cut-off, highest first</caption>' +
    '<thead><tr role="row"><th scope="col" role="columnheader">Diagnostic group</th>' +
    `<th scope="col" role="columnheader" class="axisth"><span class="sr">Probability, 0 to 100 percent</span><div class="axis" aria-hidden="true">${axis}</div></th>` +
    '<th scope="col" role="columnheader" class="num">Probability</th><th scope="col" role="columnheader" class="num">Cut-off</th>' +
    '<th scope="col" role="columnheader">Status</th></tr></thead><tbody>' +
    main.map(groupRowHTML).join("");
  if (other) {
    html += '<tr class="sep" role="row"><th colspan="5" scope="colgroup" role="columnheader">Residual category, not ranked</th></tr>' + groupRowHTML(other);
  }
  html += '</tbody></table>' +
    '<p class="legend"><span><i class="mk above"></i>At or above cut-off</span><span><i class="mk below"></i>Below cut-off</span>' +
    '<span><i class="mk tk"></i>Group cut-off</span></p>' +
    `<p class="fine">Bars show probability on a 0 to 100% scale. Probabilities are normalised to sum to 100% over the ${model.classes.length} groups. ` +
    'Status compares unrounded values. Class weights are balanced, so probabilities do not reflect how common each group is.</p>';
  if (other) html += `<p class="fine">${escapeHTML(OTHER_NOTE.replace("%d", model.performance[OTHER_KEY].n))}</p>`;
  return html;
}

function renderMeta(model) {
  const items = [
    ["Training set", `${model.n_patients.toLocaleString("en-US")} patients`],
    ["Groups", String(model.classes.length)],
    ["Items", String(model.items.length)],
    ["Model date", model.generated]
  ];
  return items.map(([k, v]) => `<div><dt>${k}</dt><dd>${escapeHTML(v)}</dd></div>`).join("");
}

function renderModelInfo(model, domains) {
  const cv = model.cv;
  const order = model.classes.filter((c) => c !== OTHER_KEY).sort((a, b) => model.performance[b].n - model.performance[a].n);
  if (model.classes.includes(OTHER_KEY)) order.push(OTHER_KEY);
  const rows = order.map((c) => {
    const p = model.performance[c];
    return `<tr${c === OTHER_KEY ? ' class="resid"' : ""}><td>${escapeHTML(model.labels[c])}</td>` +
      `<td data-label="n">${p.n}</td><td data-label="Prevalence">${pct(p.prevalence)}</td>` +
      `<td data-label="AUC">${p.auc.toFixed(3)}</td><td data-label="Cut-off">${pct(p.cutoff)}</td>` +
      `<td data-label="Youden J">${p.youden_j.toFixed(3)}</td></tr>`;
  }).join("");
  const dropped = Object.entries(model.dropped_groups)
    .map(([k, n]) => `${escapeHTML(k.split("_").map((w, i) => (i ? w.toLowerCase() : w)).join("-"))} (n = ${n})`).join("; ");
  return "<h3>Training set</h3>" +
    `<p>${model.n_patients.toLocaleString("en-US")} patients, ${model.classes.length} diagnostic groups, ${model.items.length} chief-problem items in ${domains.length} codebook domains. ` +
    "L2-penalised logistic regression, one-vs-rest, balanced class weights; group probabilities are normalised to sum to 100%.</p>" +
    "<h3>Diagnostic groups</h3>" +
    `<p>${escapeHTML(model.dx_rule)}.</p>` +
    "<h3>Performance and cut-off by group</h3>" +
    '<table class="info"><thead><tr><th>Diagnostic group</th><th>n</th><th>Prevalence</th><th>Out-of-fold AUC</th><th>Cut-off</th><th>Youden J</th></tr></thead>' +
    `<tbody>${rows}</tbody></table>` +
    "<h3>Cut-off definition</h3>" +
    `<p>Youden point (maximum of sensitivity + specificity - 1) of the out-of-fold ROC curve of each group, from ${cv.splits}-fold stratified cross-validation repeated ${cv.repeats} times (seed ${cv.seed}).</p>` +
    "<h3>Groups left out</h3>" +
    `<p>${dropped}: fewer than ${model.min_group_n} patients, so stratified cross-validation does not hold.</p>` +
    "<h3>Relation to the manuscript</h3>" +
    `<p>${escapeHTML(model.note)} It is a separate model fitted for this tool, not a model of the manuscript analysis.</p>` +
    "<h3>Limits</h3><ul><li>Internal validation only.</li>" +
    "<li>Balanced class weights: probabilities do not reflect how common each group is in practice.</li></ul>";
}

// ---------------------------------------------------------------- page
function initUI(model, domains) {
  const list = document.getElementById("domains");
  const count = document.getElementById("count");
  const panel = document.getElementById("panel");
  const compute = document.getElementById("compute");
  const getPicked = () => {
    const on = new Set(Array.from(list.querySelectorAll("input:checked"), (c) => c.value));
    return model.items.map((it) => it.name).filter((n) => on.has(n));
  };

  document.getElementById("model-meta").innerHTML = renderMeta(model);
  document.getElementById("model-info").innerHTML = renderModelInfo(model, domains);

  for (const d of domains) {
    const details = document.createElement("details");
    details.className = "dom";
    const summary = document.createElement("summary");
    const title = document.createElement("span");
    title.textContent = d.label;
    const meta = document.createElement("span");
    meta.className = "muted";
    meta.dataset.total = d.names.length;
    meta.textContent = `${d.names.length} item${d.names.length === 1 ? "" : "s"}`;
    summary.append(title, meta);
    const options = document.createElement("div");
    options.className = "options";
    for (const name of d.names) {
      const label = document.createElement("label");
      const box = document.createElement("input");
      box.type = "checkbox";
      box.value = name;
      label.append(box, document.createTextNode(name));
      options.appendChild(label);
    }
    details.append(summary, options);
    list.appendChild(details);
  }

  const refresh = () => {
    const picked = getPicked();
    count.innerHTML = countHTML(domains, picked);
    compute.disabled = !isValidCount(picked.length);
    for (const details of list.querySelectorAll("details")) {
      const k = details.querySelectorAll("input:checked").length;
      const meta = details.querySelector("summary .muted");
      const n = Number(meta.dataset.total);
      meta.textContent = `${n} item${n === 1 ? "" : "s"}` + (k ? ` · ${k} selected` : "");
    }
  };
  list.addEventListener("change", refresh);
  compute.addEventListener("click", () => { panel.innerHTML = renderResult(model, getPicked()); });
  document.getElementById("reset").addEventListener("click", () => {
    for (const box of list.querySelectorAll("input")) box.checked = false;
    panel.innerHTML = HINT;
    refresh();
  });
  panel.innerHTML = HINT;
  refresh();
}

async function start() {
  const loading = document.getElementById("loading");
  try {
    const [m, d] = await Promise.all([fetch("./model_all_groups.json"), fetch("./item_domains.json")]);
    if (!m.ok || !d.ok) throw new Error(`HTTP ${m.status} / ${d.status}`);
    const model = await m.json();
    const domains = buildDomains(model, await d.json());
    initUI(model, domains);
    loading.hidden = true;
    document.getElementById("tool-layout").hidden = false;
  } catch (err) {
    loading.className = "load-error";
    loading.textContent = "The model files could not be loaded (" + err.message + "). " +
      "Open the page through a web server, not from disk; for a local copy run: python -m http.server";
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { buildDomains, probabilities, rankGroups, renderResult, renderModelInfo, renderMeta, countHTML, selectionState, isValidCount };
}
if (typeof document !== "undefined") document.addEventListener("DOMContentLoaded", start);
