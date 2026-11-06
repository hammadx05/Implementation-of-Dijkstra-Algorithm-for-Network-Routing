# NPS — Dijkstra Network Routing Tool

A command-line and web-based network routing simulator that computes shortest
paths in a link-state network using **Dijkstra's Algorithm**. Built for the
**Network Protocols and Standards (NPS)** course project.

The tool accepts a user-defined network topology, computes optimal paths from a
chosen source node, generates a next-hop routing table, visualizes the results
both statically (Matplotlib PNG) and interactively (web dashboard), and exports
results as CSV or JSON.

---

## Project Information

| Field | Value |
|---|---|
| **Course** | Network Protocols and Standards (NPS) |
| **Instructor** | Mr. Shoaib Raza |
| **Group Members** | Muhammad Hammad (23K-2005), Muhammad Sami Ashfaq (23K-2031) |
| **Reference topology** | 12 nodes, 21 bidirectional links |

---

## Features

- **Topology input** — parse CSV-style text (`Node1, Node2, Cost`), with
  comments (`#`) and duplicate-edge handling (keeps lower cost).
- **Validation** — rejects negative costs, malformed lines, self-loops, and
  missing source nodes with clear error messages. Reports unreachable nodes
  instead of crashing.
- **Random topology generator** — connected graphs with a **minimum of 10
  nodes** (default 12), configurable edge density and seed.
- **Dijkstra shortest-path engine** — computes shortest paths from any source to
  all reachable destinations and builds the shortest-path tree.
- **Routing table generation** — next-hop forwarding table per destination, like
  a real router maintains.
- **Path query** — shortest path and cost between any two specific nodes.
- **Web dashboard** (Flask + Cytoscape.js) — interactive topology graph, routing
  table, path highlighting, live statistics, and export buttons.
- **Matplotlib visualizations** — full topology, shortest-path tree, and
  highlighted path rendered as PNG.
- **Export module** — routing tables and Dijkstra results to CSV or JSON.

---

## Project Structure

```
nps_routing/
├── run.py                     # CLI entry point + dashboard launcher
├── requirements.txt           # Python dependencies
├── README.md                  # this file
├── NOTES_FOR_REPORTS.md       # guidance for the written report
├── topologies/
│   └── reference_12.txt       # 12-node reference topology (≥10 nodes)
├── data/
│   └── sample_10.txt          # 10-node sample topology (≥10 nodes)
├── core/
│   ├── topology.py            # parsing, validation, random generation
│   ├── dijkstra.py            # shortest-path engine
│   ├── routing.py             # routing table generation
│   └── export.py              # CSV / JSON export
├── viz/
│   └── static_plot.py         # Matplotlib visualizations
├── emulation/
│   └── mininet_runner.py      # optional Mininet module (not in final build)
├── web/
│   ├── app.py                 # Flask app + REST API
│   ├── templates/
│   │   └── dashboard.html     # dashboard UI
│   └── static/
│       ├── dashboard.js
│       └── style.css
└── tests/
    └── test_core.py           # 9 sanity tests for core logic
```

---

## Requirements

- **Python** 3.10 or newer (developed on Python 3.14)
- **pip** and **venv** (Kali/Debian: `sudo apt install python3-full python3-venv`)
- A modern web browser (for the dashboard)
- Internet access on first run (to load Cytoscape.js from CDN), or offline
  fallback as noted in *Troubleshooting* below.

Runtime dependencies (installed via `requirements.txt`):

- `networkx>=3.0` — graph construction and Dijkstra implementation
- `matplotlib>=3.7` — static PNG visualization
- `flask>=3.0` — dashboard backend
- `pytest>=8.0` — test runner

---

## Installation

Kali's Python is "externally managed" (PEP 668), so you must use a virtual
environment. Do **not** run `pip install` globally or use
`--break-system-packages`.

### 1. Clone or extract the project

```bash
cd ~/Desktop
# If you received the project as an archive, extract it here.
# Otherwise `cd` into the existing `nps_routing` directory.
cd nps_routing
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt should now show `(.venv)`.

If `python3 -m venv` fails, install the venv module first:

```bash
sudo apt update
sudo apt install -y python3-full python3-venv python3-pip
```

Then repeat the `python3 -m venv .venv` command.

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify the installation

```bash
python -m pytest -q tests/
```

Expected output: `9 passed in <1s`.

---

## Usage

> **Important:** Every time you open a new terminal, activate the virtual
> environment first:
>
> ```bash
> cd ~/Desktop/nps_routing
> source .venv/bin/activate
> ```

### Web dashboard (recommended)

```bash
python run.py dashboard
```

Then open **http://127.0.0.1:5000** in a browser. The 12-node reference topology
loads automatically. From the dashboard you can:

- **Load** the reference (12 nodes), sample (10 nodes), a random topology, or a
  custom uploaded file / pasted text.
- **Run Dijkstra** from any selected source node — the routing table fills and
  the shortest-path tree edges turn green on the graph.
- **Query a path** between two nodes — the path highlights orange and the cost
  is displayed.
- **Export** the routing table as CSV or JSON, and download PNG diagrams of the
  topology, tree, or highlighted path.

Press `Ctrl+C` in the terminal to stop the server.

### Command-line interface

```bash
# Print topology summary, distances, and routing table
python run.py analyze --topology topologies/reference_12.txt --source R1

# Query the shortest path between two nodes
python run.py path --topology topologies/reference_12.txt --source R1 --destination R12

# Generate a random connected topology (minimum 10 nodes)
python run.py random --nodes 15 --prob 0.4 --out topologies/random_15.txt

# Render a static PNG
python run.py plot --topology topologies/reference_12.txt --kind tree --source R1 --out tree.png

# Export the routing table to CSV or JSON
python run.py analyze --topology topologies/reference_12.txt --source R1 --export routing.csv
python run.py analyze --topology topologies/reference_12.txt --source R1 --export routing.json
```

Run `python run.py --help` or `python run.py <command> --help` for details.

### Topology file format

One link per line, `Node1, Node2, Cost`:

```
# 12-node reference topology (bidirectional links)
R1, R2, 4
R1, R3, 2
R1, R4, 7
R2, R3, 1
...
```

- Blank lines and lines starting with `#` are ignored.
- Cost must be a **non-negative number**.
- Links are **bidirectional** by default.
- Neighbour relationships are inferred from the links — no separate list needed.
- Duplicate edges keep the **lower** cost.

---

## Reference Topology (12 nodes, 21 links)

`topologies/reference_12.txt`:

```
R1, R2, 4      R1, R3, 2      R1, R4, 7
R2, R3, 1      R2, R5, 5      R3, R4, 3
R3, R5, 6      R4, R6, 2      R4, R7, 8
R5, R6, 4      R5, R8, 3      R6, R7, 1
R6, R8, 5      R7, R9, 2      R7, R10, 6
R8, R9, 3      R8, R11, 4     R9, R10, 1
R9, R12, 5     R10, R11, 2    R11, R12, 3
```

Sample `analyze` output from `R1`:

```
Shortest distances from R1:
  R1     0
  R2     3.0     R3     2.0     R4     5.0
  R5     8.0     R6     7.0     R7     8.0
  R8     11.0    R9     10.0    R10    11.0
  R11    13.0    R12    15.0

Routing table (excerpt):
  dest=R10  next_hop=R3  cost=11.0  path=R1 -> R3 -> R4 -> R6 -> R7 -> R9 -> R10
  dest=R12  next_hop=R3  cost=15.0  path=R1 -> R3 -> R4 -> R6 -> R7 -> R9 -> R12
```

Note that every next-hop from R1 is R3 because R3 is R1's cheapest neighbor
(cost 2) and lies on the shortest path to every other node — a valid link-state
outcome.

---

## Validation Rules

The tool rejects the following inputs at parse time with a clear `TopologyError`:

| Invalid input | Reason |
|---|---|
| `A, B` (2 fields) | Malformed line — expected 3 fields |
| `A, B, xyz` | Non-numeric cost |
| `A, B, -3` | Negative cost — Dijkstra requires non-negative weights |
| `A, A, 2` | Self-loop |
| `, B, 2` | Empty node name |
| Source node not in graph | Missing source — reported, not crashed |

Unreachable nodes (in a disconnected topology) are **reported** in the
`unreachable` field of Dijkstra results, not treated as errors.

---

## Testing

```bash
python -m pytest -q tests/
```

Tests cover parsing, validation, Dijkstra correctness (hand-verified against the
reference topology), path queries, routing table generation, random generator
minimum-size enforcement, and reachability reporting.

---

## Optional Mininet Module

The proposal lists Mininet emulation as **optional**. The module
`emulation/mininet_runner.py` exists in the codebase but is **not part of the
final delivered build** because of environment-specific incompatibilities on the
development machine (Kali Linux, Mininet 2.3.0, Open vSwitch 4.0.0). End-to-end
ping reachability inside Mininet could not be achieved reliably within the demo
window; this is documented as an environment constraint, not an algorithmic
limitation.

Per the proposal's scope boundaries, the core routing simulator is delivered as a
complete, standalone tool.

---

## Troubleshooting

### `error: externally-managed-environment` when running `pip install`

Kali's system Python is managed by `apt` (PEP 668). Create and activate a
virtual environment as shown in the installation section. Do not use
`--break-system-packages`.

### `python -m pytest` says "No module named pytest"

You're using the system Python, not the venv. Activate the venv first:

```bash
source .venv/bin/activate
```

### Dashboard loads but the graph panel is blank

The browser couldn't fetch Cytoscape.js from `unpkg.com`. Download the JS files
locally and point the HTML at them:

```bash
cd web/static
curl -fLO https://unpkg.com/cytoscape@3.28.1/dist/cytoscape.min.js
curl -fLO https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js
```

Then edit `web/templates/dashboard.html` and replace the two `<script
src="https://unpkg.com/...">` lines with:

```html
<script src="/static/cytoscape.min.js"></script>
<script src="/static/cytoscape-dagre.js"></script>
```

Reload the page.

### `Address already in use` on `python run.py dashboard`

Another process is on port 5000. Either stop it or use a different port:

```bash
python run.py dashboard --port 5001
```

### Matplotlib complains about a display / backend

`viz/static_plot.py` forces the headless `Agg` backend, so PNG export works
without a display. If you see a warning, it's harmless.

---

## License

Educational project — no license attached. Reuse for academic purposes only.

---

## References

1. Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2009).
   *Introduction to Algorithms* (3rd ed.). MIT Press. Chapter 24.
2. Dijkstra, E. W. (1959). "A note on two problems in connexion with graphs."
   *Numerische Mathematik*, 1(1), 269–271.
3. Moy, J. (1998). *OSPF Version 2*. RFC 2328, IETF.
4. NetworkX Developers. *NetworkX Documentation — Shortest Paths*.
5. Hunter, J. D. (2007). "Matplotlib: A 2D graphics environment."
   *Computing in Science & Engineering*, 9(3), 90–95.
6. Flask Documentation. https://flask.palletsprojects.com/
7. Cytoscape.js Documentation. https://js.cytoscape.org/
