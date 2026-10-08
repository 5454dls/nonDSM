"use strict";

// Direct browser port of app.py. Does NOT fit a model or send selected symptoms to a server.
// Reference: model_all_groups.json / item_domains.json (identical to the Python inputs).
const MIN_ITEMS = 3;
const MAX_ITEMS = 10;
const OTHER_KEY = "Other";
const CITATION = "[OO]"; // Replace with the manuscript citation after acceptance.
const OTHER_NOTE =
  "Other diagnoses includes: personality disorders, neurocognitive disorders, " +
  "dementia, and substance- or alcohol-related diagnoses, among diagnoses that do " +
  "not match the other six groups' keywords (n = %d in the training set).";
const HINT = '<p class="hint">Select chief problems, then press Compute.</p>';

let model;
let domains;
let names;

const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[char]);
const pct = (x) => (100 * x).toFixed(1) + "%";

function buildDomains(data, domainData) {
  if (!Array.isArray(data.items) || !Array.isArray(data.classes) || !Array.isArray(domainData.domains)) {
    throw new Error("The model or domain JSON has an unexpected structure.");
  }
  const codeToName = new Map(data.items.map((it) => [it.code, it.name]));
  const built = domainData.domains.map((entry) => ({
    label: entry.label,
    names: entry.codes.map((code) => {
      if (!codeToName.has(code)) throw new Error("Unknown item code: " + code);
      return codeToName.get(code);
    })
  }));
  const assigned = built.flatMap((entry) => entry.names);
  if (assigned.length !== data.items.length || new Set(assigned).size !== data.items.length ||
      data.items.some((it) => !assigned.includes(it.name))) {
    throw new Error("The item domains do not match the model items.");
  }
  if (new Set(data.items.map((it) => it.name)).size !== data.items.length) {
    throw new Error("Duplicate item name in the model.");
  }
  for (const c of data.classes) {
    if (!Array.isArray(data.coef?.[c]) || data.coef[c].length !== data.items.length ||
        !Number.isFinite(data.intercept?.[c]) || !Number.isFinite(data.performance?.[c]?.cutoff)) {
      throw new Error("Incomplete model coefficients for " + c);
    }
  }
  return built;
}

// Match app.py _probs: for each group, dot product over ALL items in model order,
// followed by logistic sigmoid, then normalisation of the seven group scores.
function calculateProbabilities(data, selectedNames) {
  const inputSet = new Set(selectedNames);
  const x = data.items.map((it) => inputSet.has(it.name) ? 1.0 : 0.0);
  const raw = {};
  for (const c of data.classes) {
    let z = data.intercept[c];
    // A left-to-right sum (as in Python's sum()) limits floating-point differences.
    let dot = 0.0;
    for (let i = 0; i < x.length; i++) dot += data.coef[c][i] * x[i];
    z += dot;
    raw[c] = 1.0 / (1.0 + Math.exp(-z));
  }
  let total = 0.0;
  for (const c of data.classes) total += raw[c];
  const probability = {};
  for (const c of data.classes) probability[c] = raw[c] / total;
  return probability;
}

function getSelected() {
  const selected = new Set(Array.from(document.querySelectorAll('#domains input[type="checkbox"]:checked'),
    (checkbox) => checkbox.value));
  return names.filter((name) => selected.has(name)); // Preserve model/codebook order.
}

function countHTML(picked) {
  const n = picked.length;
  let state = "Ready to compute.";
  if (n === 0) state = `Select ${MIN_ITEMS} to ${MAX_ITEMS}.`;
  else if (n < MIN_ITEMS) state = `Select ${MIN_ITEMS - n} more (minimum ${MIN_ITEMS}).`;
  else if (n > MAX_ITEMS) state = `Remove ${n - MAX_ITEMS} (maximum ${MAX_ITEMS}).`;
  let html = `<p class="cnt"><b>${n} selected</b> <span class="st">&middot; ${state}</span></p>`;
  if (n > 0) {
    const chosen = new Set(picked);
    const lines = [];
    for (const domain of domains) {
      const subset = domain.names.filter((name) => chosen.has(name));
      if (subset.length) {
        lines.push(`<li><b>${escapeHTML(domain.label)}</b> <span>${subset.length} of ${domain.names.length}</span><br>${subset.map(escapeHTML).join("; ")}</li>`);
      }
    }
    html += `<ul class="sel">${lines.join("")}</ul>`;
  }
  return html;
}

function axisHeader() {
  return '<div class="axis" aria-hidden="true">' + [0, 25, 50, 75, 100]
    .map((tick) => `<span style="left:${tick}%">${tick}%</span>`).join("") + "</div>";
}

function resultRow(data, rank, cls, probability) {
  const p = probability[cls];
  const cut = data.performance[cls].cutoff;
  const over = p >= cut; // Use unrounded values, as in app.py.
  const kind = over ? "above" : "below";
  const grid = [25, 50, 75].map((tick) => `<i class="g" style="left:${tick}%"></i>`).join("");
  return `<tr class="${kind}"><td class="rk">${rank}</td><th scope="row">${escapeHTML(data.labels[cls])}</th>` +
    `<td class="bar"><div class="track" aria-hidden="true">${grid}` +
    `<div class="fill ${kind}" style="width:${(100 * Math.min(p, 1)).toFixed(2)}%"></div>` +
    `<div class="tick" style="left:${(100 * Math.min(cut, 1)).toFixed(2)}%"></div></div></td>` +
    `<td class="n v">${pct(p)}</td><td class="n">${pct(cut)}</td>` +
    `<td class="st"><span class="mk ${kind}"></span>${over ? "At or above" : "Below"}</td></tr>`;
}

function renderResult(data, selectedNames) {
  const valid = new Set(data.items.map((it) => it.name));
  const picked = [...new Set(selectedNames.filter((name) => valid.has(name)))];
  if (picked.length < MIN_ITEMS || picked.length > MAX_ITEMS) {
    return `<p class="hint">Select between ${MIN_ITEMS} and ${MAX_ITEMS} chief problems. You selected ${picked.length}.</p>`;
  }
  const order = new Map(data.items.map((it, i) => [it.name, i]));
  picked.sort((a, b) => order.get(a) - order.get(b));
  const prob = calculateProbabilities(data, picked);
  const sortedAll = [...data.classes].sort((a, b) => prob[b] - prob[a]);
  const named = sortedAll.filter((cls) => cls !== OTHER_KEY);
  const over = sortedAll.filter((cls) => prob[cls] >= data.performance[cls].cutoff);
  const line = over.length
    ? `${over.length} of ${data.classes.length} groups at or above their cut-off: ${over.map((cls) => data.labels[cls]).join("; ")}.`
    : "No group reaches its cut-off.";

  let html = '<p class="res-title">Result</p>' +
    `<p class="echo"><b>Input (${picked.length}):</b> ${picked.map(escapeHTML).join("; ")}</p>` +
    `<p class="summary">${escapeHTML(line)}</p>` +
    '<div class="table-scroll" role="region" aria-label="Result table" tabindex="0">' +
    '<table class="rt"><caption class="sr">Probability of each diagnostic group with its cut-off</caption>' +
    '<thead><tr><th>#</th><th>Diagnostic group</th>' +
    `<th class="axisth"><span class="sr">Probability scale, 0 to 100 percent</span>${axisHeader()}</th>` +
    '<th class="n">Probability</th><th class="n">Cut-off</th><th style="padding-left:12px">Status</th>' +
    '</tr></thead><tbody>';
  named.forEach((cls, i) => { html += resultRow(data, i + 1, cls, prob); });
  if (data.classes.includes(OTHER_KEY)) {
    html += '<tr class="sep"><th colspan="6" scope="colgroup">Residual category, not ranked</th></tr>';
    html += resultRow(data, "&ndash;", OTHER_KEY, prob);
  }
  html += '</tbody></table></div>' +
    '<p class="legend"><span><i class="mk above"></i>At or above the group cut-off</span>' +
    '<span><i class="mk below"></i>Below</span><span><i class="mk tk"></i>Group cut-off</span></p>' +
    `<p class="fine">Probabilities are normalised to sum to 100% over the ${data.classes.length} groups. ` +
    'Status compares unrounded values. Balanced class weights mean the probabilities do not reflect how common each group is.</p>';
  if (data.classes.includes(OTHER_KEY)) {
    html += `<p class="fine">${escapeHTML(OTHER_NOTE.replace("%d", data.performance[OTHER_KEY].n))}</p>`;
  }
  return html;
}

function renderModelInfo(data, domainList) {
  const cv = data.cv;
  const sorted = data.classes.filter((c) => c !== OTHER_KEY)
    .sort((a, b) => data.performance[b].n - data.performance[a].n);
  if (data.classes.includes(OTHER_KEY)) sorted.push(OTHER_KEY);
  const rows = sorted.map((cls) => {
    const p = data.performance[cls];
    return `<tr${cls === OTHER_KEY ? ' class="resid"' : ""}><td>${escapeHTML(data.labels[cls])}</td>` +
      `<td>${p.n}</td><td>${pct(p.prevalence)}</td><td>${p.auc.toFixed(3)}</td>` +
      `<td>${pct(p.cutoff)}</td><td>${p.youden_j.toFixed(3)}</td></tr>`;
  }).join("");
  const dropped = Object.entries(data.dropped_groups).map(([key, n]) =>
    `${escapeHTML(key.replaceAll("_", " "))} (n = ${n})`).join("; ");
  return `<h3>Training set</h3><p>${data.n_patients} patients, ${data.classes.length} diagnostic groups, ` +
    `${data.items.length} chief-problem items in ${domainList.length} codebook domains. ` +
    'Model: L2-penalised logistic regression, one-vs-rest, balanced class weights. ' +
    'The group probabilities are normalised to sum to 100%.</p>' +
    '<h3>Performance and cut-off by group</h3>' +
    '<div class="info-scroll"><table><thead><tr><th>Diagnostic group</th><th>n</th><th>Prevalence</th>' +
    '<th>Out-of-fold AUC</th><th>Cut-off</th><th>Youden J</th></tr></thead><tbody>' +
    rows + '</tbody></table></div>' +
    '<h3>Cut-off definition</h3>' +
    `<p>The cut-off of each group is the Youden point (maximum of sensitivity + specificity ` +
    `- 1) of its out-of-fold ROC curve, from ${cv.splits}-fold stratified cross-validation ` +
    `repeated ${cv.repeats} times (seed ${cv.seed}).</p>` +
    '<h3>Groups left out</h3>' +
    `<p>${dropped}: fewer than ${data.min_group_n} patients, so stratified cross-validation does not hold.</p>` +
    '<h3>How this differs from the manuscript</h3>' +
    `<p>The manuscript reports four diagnostic groups. This tool is refitted on all ${data.n_patients} ` +
    `patients across ${data.classes.length} groups, so its coefficients and performance are not the manuscript's.</p>` +
    '<h3>Limits</h3><ul><li>Internal validation only.</li>' +
    '<li>Balanced class weights mean these probabilities do not reflect how common each group is in practice.</li>' +
    '<li>This tool does not make a diagnosis.</li></ul>';
}

function renderUI(data, domainList) {
  document.getElementById("model-meta").innerHTML =
    `<div><dt>Model</dt><dd>refitted on ${data.n_patients} patients, ${data.classes.length} groups, ${data.items.length} items</dd></div>` +
    `<div><dt>Generated</dt><dd>${escapeHTML(data.generated)}</dd></div>` +
    `<div><dt>Diagnostic-group rule</dt><dd>${escapeHTML(data.dx_rule)}</dd></div>` +
    `<div><dt>Citation</dt><dd>${escapeHTML(CITATION)}</dd></div>`;
  const list = document.getElementById("domains");
  list.replaceChildren();
  for (const domain of domainList) {
    const details = document.createElement("details");
    details.className = "dom";
    const summary = document.createElement("summary");
    summary.textContent = `${domain.label} · ${domain.names.length} item${domain.names.length === 1 ? "" : "s"}`;
    details.appendChild(summary);
    const options = document.createElement("div");
    options.className = "options";
    for (const name of domain.names) {
      const label = document.createElement("label");
      label.className = "option";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = name;
      const span = document.createElement("span");
      span.textContent = name;
      label.append(checkbox, span);
      options.appendChild(label);
    }
    details.appendChild(options);
    list.appendChild(details);
  }
  document.getElementById("model-info").innerHTML = renderModelInfo(data, domainList);
  const count = document.getElementById("count");
  count.innerHTML = countHTML([]);
  list.addEventListener("change", (event) => {
    if (event.target.matches('input[type="checkbox"]')) count.innerHTML = countHTML(getSelected());
  });
  // Match Gradio: changing checkboxes updates the count, but NEVER recomputes results.
  document.getElementById("compute").addEventListener("click", () => {
    document.getElementById("panel").innerHTML = renderResult(data, getSelected());
  });
  document.getElementById("reset").addEventListener("click", () => {
    for (const checkbox of list.querySelectorAll('input[type="checkbox"]')) checkbox.checked = false;
    count.innerHTML = countHTML([]);
    document.getElementById("panel").innerHTML = HINT;
  });
}

async function initialize() {
  const loading = document.getElementById("loading");
  try {
    const [resModel, resDomains] = await Promise.all([
      fetch("./model_all_groups.json"), fetch("./item_domains.json")
    ]);
    if (!resModel.ok || !resDomains.ok) {
      throw new Error(`Could not load JSON (${resModel.status}, ${resDomains.status}).`);
    }
    const [data, domainData] = await Promise.all([resModel.json(), resDomains.json()]);
    model = data;
    names = model.items.map((it) => it.name);
    domains = buildDomains(model, domainData);
    renderUI(model, domains);
    loading.hidden = true;
    document.getElementById("tool-layout").hidden = false;
  } catch (error) {
    console.error("Unable to initialise the model:", error);
    loading.classList.add("error");
    loading.textContent = "Could not load the research model. Check that index.html, script.js, style.css and both JSON files are all uploaded to the same GitHub folder. " + error.message;
  }
}

// The core can also be checked against the original Python app with Node.js.
if (typeof module !== "undefined" && module.exports) {
  module.exports = { calculateProbabilities, renderResult, buildDomains, countHTML, renderModelInfo };
}
if (typeof document !== "undefined") document.addEventListener("DOMContentLoaded", initialize);
