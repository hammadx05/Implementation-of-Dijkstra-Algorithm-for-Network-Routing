"""Flask dashboard + REST API."""
from __future__ import annotations

import io
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from core.dijkstra import run_dijkstra, shortest_path_between
from core.export import routing_table_to_csv, routing_table_to_json, dijkstra_result_to_json
from core.routing import build_routing_table
from core.topology import (
    TopologyError,
    generate_random_topology,
    parse_topology_file,
    parse_topology_text,
    summary,
    topology_to_text,
)
from viz.static_plot import (
    plot_highlighted_path,
    plot_shortest_path_tree,
    plot_topology,
)

app = Flask(__name__, template_folder="templates", static_folder="static")

# In-memory current topology (single-user educational tool)
STATE: dict = {
    "graph": None,
    "name": None,
    "text": None,
    "source": None,
}


def _load(graph, name: str, text: str | None = None):
    STATE["graph"] = graph
    STATE["name"] = name
    STATE["text"] = text or topology_to_text(graph)
    STATE["source"] = sorted(graph.nodes)[0]


@app.get("/")
def index():
    return render_template("dashboard.html")


@app.get("/api/status")
def api_status():
    if STATE["graph"] is None:
        return jsonify({"loaded": False})
    g = STATE["graph"]
    return jsonify({
        "loaded": True,
        "name": STATE["name"],
        "summary": summary(g),
        "source": STATE["source"],
        "edges": [
            {"u": u, "v": v, "weight": d["weight"]}
            for u, v, d in g.edges(data=True)
        ],
        "nodes": sorted(g.nodes),
        "text": STATE["text"],
    })


@app.post("/api/load-text")
def api_load_text():
    payload = request.get_json(force=True)
    text = payload.get("text", "")
    try:
        parsed = parse_topology_text(text)
    except TopologyError as e:
        return jsonify({"error": str(e)}), 400
    _load(parsed.graph, payload.get("name", "custom"), text)
    return api_status()


@app.post("/api/load-file")
def api_load_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    f = request.files["file"]
    text = f.read().decode("utf-8")
    try:
        parsed = parse_topology_text(text)
    except TopologyError as e:
        return jsonify({"error": str(e)}), 400
    _load(parsed.graph, f.filename or "uploaded", text)
    return api_status()


@app.get("/api/reference")
def api_reference():
    path = Path(__file__).resolve().parent.parent / "topologies" / "reference_12.txt"
    parsed = parse_topology_file(path)
    _load(parsed.graph, "reference_12", path.read_text())
    return api_status()


@app.get("/api/sample10")
def api_sample10():
    path = Path(__file__).resolve().parent.parent / "data" / "sample_10.txt"
    parsed = parse_topology_file(path)
    _load(parsed.graph, "sample_10", path.read_text())
    return api_status()


@app.post("/api/random")
def api_random():
    payload = request.get_json(force=True) or {}
    try:
        parsed = generate_random_topology(
            n_nodes=int(payload.get("n_nodes", 12)),
            edge_probability=float(payload.get("edge_probability", 0.35)),
            seed=payload.get("seed"),
        )
    except TopologyError as e:
        return jsonify({"error": str(e)}), 400
    _load(parsed.graph, "random", topology_to_text(parsed.graph))
    return api_status()


@app.post("/api/dijkstra")
def api_dijkstra():
    if STATE["graph"] is None:
        return jsonify({"error": "No topology loaded."}), 400
    payload = request.get_json(force=True) or {}
    source = payload.get("source", STATE["source"])
    try:
        result = run_dijkstra(STATE["graph"], source)
        table = build_routing_table(STATE["graph"], source)
    except TopologyError as e:
        return jsonify({"error": str(e)}), 400
    STATE["source"] = source
    return jsonify({
        "result": result,
        "routing_table": table,
    })


@app.post("/api/path")
def api_path():
    if STATE["graph"] is None:
        return jsonify({"error": "No topology loaded."}), 400
    payload = request.get_json(force=True) or {}
    s = payload.get("source")
    d = payload.get("destination")
    if not s or not d:
        return jsonify({"error": "source and destination are required."}), 400
    try:
        return jsonify(shortest_path_between(STATE["graph"], s, d))
    except TopologyError as e:
        return jsonify({"error": str(e)}), 400


# ---- Export endpoints -------------------------------------------------------

@app.post("/api/export/routing.csv")
def api_export_routing_csv():
    payload = request.get_json(force=True) or {}
    source = payload.get("source", STATE["source"])
    rows = build_routing_table(STATE["graph"], source)
    data = routing_table_to_csv(rows).encode("utf-8")
    return send_file(io.BytesIO(data), mimetype="text/csv",
                     as_attachment=True, download_name=f"routing_{source}.csv")


@app.post("/api/export/routing.json")
def api_export_routing_json():
    payload = request.get_json(force=True) or {}
    source = payload.get("source", STATE["source"])
    rows = build_routing_table(STATE["graph"], source)
    data = routing_table_to_json(rows).encode("utf-8")
    return send_file(io.BytesIO(data), mimetype="application/json",
                     as_attachment=True, download_name=f"routing_{source}.json")


@app.post("/api/export/dijkstra.json")
def api_export_dijkstra_json():
    payload = request.get_json(force=True) or {}
    source = payload.get("source", STATE["source"])
    result = run_dijkstra(STATE["graph"], source)
    data = dijkstra_result_to_json(result).encode("utf-8")
    return send_file(io.BytesIO(data), mimetype="application/json",
                     as_attachment=True, download_name=f"dijkstra_{source}.json")


# ---- Static PNG plots -------------------------------------------------------

@app.get("/api/plot/topology.png")
def api_plot_topology():
    if STATE["graph"] is None:
        return jsonify({"error": "No topology loaded."}), 400
    png = plot_topology(STATE["graph"], f"Topology: {STATE['name']}")
    return send_file(io.BytesIO(png), mimetype="image/png")


@app.get("/api/plot/tree.png")
def api_plot_tree():
    if STATE["graph"] is None:
        return jsonify({"error": "No topology loaded."}), 400
    source = request.args.get("source", STATE["source"])
    result = run_dijkstra(STATE["graph"], source)
    png = plot_shortest_path_tree(STATE["graph"], result)
    return send_file(io.BytesIO(png), mimetype="image/png")


@app.get("/api/plot/path.png")
def api_plot_path():
    if STATE["graph"] is None:
        return jsonify({"error": "No topology loaded."}), 400
    s = request.args.get("source", STATE["source"])
    d = request.args.get("destination")
    r = shortest_path_between(STATE["graph"], s, d)
    if not r["reachable"]:
        return jsonify({"error": "No path between nodes."}), 400
    png = plot_highlighted_path(STATE["graph"], r["path"], s, d, r["cost"])
    return send_file(io.BytesIO(png), mimetype="image/png")


def main(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    # Pre-load the reference topology
    try:
        ref = Path(__file__).resolve().parent.parent / "topologies" / "reference_12.txt"
        parsed = parse_topology_file(ref)
        _load(parsed.graph, "reference_12", ref.read_text())
    except Exception:
        pass
    app.run(host=host, port=port, debug=debug)
