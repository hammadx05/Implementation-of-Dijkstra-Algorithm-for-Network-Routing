"use strict";

const $ = (id) => document.getElementById(id);
let cy = null;
let lastSource = null;

// ---------------- Cytoscape setup -----------------------------------------
function initCy() {
  cy = cytoscape({
    container: $("cy"),
    style: [
      { selector: "node", style: {
          "background-color": "#4C72B0",
          "label": "data(label)",
          "color": "#e2e8f0",
          "font-size": 11,
          "text-valign": "center",
          "text-halign": "center",
          "width": 34, "height": 34,
          "border-width": 2, "border-color": "#0b1220",
      }},
      { selector: "node.source", style: { "background-color": "#C44E52", "width": 42, "height": 42 }},
      { selector: "node.dest",   style: { "background-color": "#8172B2", "width": 42, "height": 42 }},
      { selector: "node.onpath", style: { "border-color": "#DD8452", "border-width": 4 }},
      { selector: "edge", style: {
          "width": 2,
          "line-color": "#475569",
          "target-arrow-shape": "none",
          "curve-style": "bezier",
          "label": "data(weight)",
          "font-size": 10,
          "color": "#94a3b8",
          "text-background-color": "#0b1220",
          "text-background-opacity": 0.85,
          "text-background-padding": 2,
      }},
      { selector: "edge.onpath", style: { "line-color": "#DD8452", "width": 4, "color": "#DD8452" }},
      { selector: "edge.tree",   style: { "line-color": "#55A868", "width": 3 }},
    ],
    layout: { name: "cose", animate: false },
    wheelSensitivity: 0.2,
  });
}

function renderGraph(nodes, edges) {
  cy.elements().remove();
  cy.add(nodes.map((n) => ({ data: { id: n, label: n } })));
  cy.add(edges.map((e) => ({
    data: { id: `${e.u}__${e.v}`, source: e.u, target: e.v, weight: e.weight },
  })));
  cy.layout({ name: "cose", animate: false, fit: true, padding: 30 }).run();
}

function clearHighlights() {
  cy.nodes().removeClass("source dest onpath");
  cy.edges().removeClass("onpath tree");
}

// ---------------- UI helpers ----------------------------------------------
function fillSelect(select, values, selected) {
  select.innerHTML = "";
  values.forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v; opt.textContent = v;
    if (v === selected) opt.selected = true;
    select.appendChild(opt);
  });
}

function setStatus(data) {
  if (!data.loaded) {
    $("status-card").innerHTML = "<span>No topology loaded.</span>";
    return;
  }
  const s = data.summary;
  $("status-card").innerHTML =
    `<b>${data.name}</b> &mdash; ${s.nodes} nodes, ${s.edges} edges, ` +
    `density ${s.density.toFixed(2)}, ` +
    `${s.connected ? "connected" : "disconnected"}`;
}

function renderStats(result) {
  const reachable = Object.keys(result.distances).length;
  const unreachable = result.unreachable.length;
  const avg = reachable > 0
    ? (Object.values(result.distances).reduce((a, b) => a + b, 0) / reachable).toFixed(2)
    : "—";
  $("stats").innerHTML = `
    <div class="stat"><div class="label">Source</div><div class="value">${result.source}</div></div>
    <div class="stat"><div class="label">Reachable</div><div class="value">${reachable}</div></div>
    <div class="stat"><div class="label">Unreachable</div><div class="value">${unreachable}</div></div>
    <div class="stat"><div class="label">Avg Cost</div><div class="value">${avg}</div></div>
  `;
  $("unreachable").textContent = unreachable
    ? `Unreachable nodes: ${result.unreachable.join(", ")}`
    : "";
}

function renderTable(rows) {
  const tbody = document.querySelector("#routing-table tbody");
  tbody.innerHTML = "";
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${r.destination}</td>` +
      `<td>${r.next_hop}</td>` +
      `<td>${r.cost}</td>` +
      `<td>${r.path.join(" &rarr; ")}</td>`;
    tbody.appendChild(tr);
  });
}

// ---------------- API calls ------------------------------------------------
async function api(path, body) {
  const opts = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : {};
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

async function refreshStatus(data) {
  const st = data || await api("/api/status");
  setStatus(st);
  if (st.loaded) {
    renderGraph(st.nodes, st.edges);
    fillSelect($("source-select"), st.nodes, st.source);
    fillSelect($("q-source"), st.nodes, st.source);
    fillSelect($("q-dest"), st.nodes, st.nodes[1] || st.source);
    $("topology-text").value = st.text;
  }
  return st;
}

async function runDijkstra() {
  const source = $("source-select").value;
  const data = await api("/api/dijkstra", { source });
  lastSource = source;
  renderStats(data.result);
  renderTable(data.routing_table);
  clearHighlights();
  cy.nodes().removeClass("source");
  cy.getElementById(source).addClass("source");
  cy.edges().forEach((e) => {
    const u = e.data("source"), v = e.data("target");
    if (data.result.tree_edges.some(([a, b]) => (a === u && b === v) || (a === v && b === u))) {
      e.addClass("tree");
    }
  });
}

async function queryPath() {
  const source = $("q-source").value;
  const destination = $("q-dest").value;
  clearHighlights();
  cy.getElementById(source).addClass("source");
  cy.getElementById(destination).addClass("dest");

  const r = await api("/api/path", { source, destination });
  const box = $("query-result");
  if (!r.reachable) {
    box.innerHTML = `<span class="warn">No path from ${source} to ${destination}.</span>`;
    return;
  }
  box.innerHTML =
    `<b>${source} &rarr; ${destination}</b> &mdash; cost <b>${r.cost}</b><br>` +
    r.path.join(" &rarr; ");
  r.path.forEach((n) => cy.getElementById(n).addClass("onpath"));
  for (let i = 0; i < r.path.length - 1; i++) {
    const a = r.path[i], b = r.path[i + 1];
    cy.edges().filter((e) => (e.data("source") === a && e.data("target") === b)
                          || (e.data("source") === b && e.data("target") === a))
      .addClass("onpath");
  }
}

// ---------------- Event wiring --------------------------------------------
$("btn-load-ref").onclick = async () => refreshStatus(await api("/api/reference"));
$("btn-load-sample").onclick = async () => refreshStatus(await api("/api/sample10"));

$("btn-random").onclick = async () => {
  try {
    const n = parseInt($("rand-nodes").value, 10);
    const p = parseFloat($("rand-prob").value);
    refreshStatus(await api("/api/random", { n_nodes: n, edge_probability: p }));
  } catch (e) { alert(e.message); }
};

$("btn-upload").onclick = async () => {
  const f = $("file-input").files[0];
  if (!f) return alert("Choose a file first.");
  const fd = new FormData();
  fd.append("file", f);
  const res = await fetch("/api/load-file", { method: "POST", body: fd });
  const data = await res.json();
  if (!res.ok) return alert(data.error || "Upload failed");
  refreshStatus(data);
};

$("btn-load-text").onclick = async () => {
  try {
    refreshStatus(await api("/api/load-text", { text: $("topology-text").value }));
  } catch (e) { alert(e.message); }
};

$("btn-run-dijkstra").onclick = () => runDijkstra().catch((e) => alert(e.message));
$("btn-query").onclick = () => queryPath().catch((e) => alert(e.message));

$("btn-export-csv").onclick = async () => {
  const source = $("source-select").value;
  const res = await fetch("/api/export/routing.csv", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source }),
  });
  downloadBlob(await res.blob(), `routing_${source}.csv`);
};

$("btn-export-json").onclick = async () => {
  const source = $("source-select").value;
  const res = await fetch("/api/export/dijkstra.json", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source }),
  });
  downloadBlob(await res.blob(), `dijkstra_${source}.json`);
};

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

$("btn-plot-topology").onclick = () => window.open("/api/plot/topology.png", "_blank");
$("btn-plot-tree").onclick = () => {
  const s = $("source-select").value;
  window.open(`/api/plot/tree.png?source=${encodeURIComponent(s)}`, "_blank");
};
$("btn-plot-path").onclick = () => {
  const s = $("q-source").value, d = $("q-dest").value;
  window.open(`/api/plot/path.png?source=${encodeURIComponent(s)}&destination=${encodeURIComponent(d)}`, "_blank");
};

// ---------------- Boot ----------------------------------------------------
initCy();
refreshStatus().catch(() => {});
