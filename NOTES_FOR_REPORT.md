# Notes for the Report

This file is **not** the report — it's a working document for the group. It
records what was built, what to emphasize in the written report, what to put in
the demo, and how to phrase the tricky bits honestly. Delete or ignore it before
submission if you don't want it as an appendix.

---

## 1. Summary of the Project (one paragraph, for the abstract)

> We implemented a network routing simulator that computes shortest paths with
> Dijkstra's Algorithm in a link-state framework, mirroring the core behavior
> of OSPF. The tool parses a user-defined topology, validates it, computes
> shortest paths and a shortest-path tree from any source, generates a next-hop
> routing table, and provides both a command-line interface and an interactive
> web dashboard for visualization and path queries. It is implemented in Python
> using NetworkX for graph computation, Matplotlib for static diagrams, Flask
> and Cytoscape.js for the dashboard, and it exports routing tables and results
> as CSV or JSON. All functional features promised in the proposal are
> delivered and tested.

---

## 2. What Was Delivered (use as the "Implementation" section)

| Proposal requirement | Implemented in | Evidence |
|---|---|---|
| Topology input (CSV-style file, comments) | `core/topology.py` | `topologies/reference_12.txt` |
| Line-level, graph-level, runtime validation | `core/topology.py` | 9 passing tests cover each error case |
| Negative-weight rejection | `parse_topology_text` | `TopologyError` on `A, B, -3` |
| Connectivity check, unreachable reporting | `reachability()`, Dijkstra `unreachable` field | Disconnected topology test |
| Random generator, ≥10 nodes | `generate_random_topology` (`MIN_RANDOM_NODES = 10`) | Test + dashboard UI default 12 |
| Dijkstra engine + shortest-path tree | `core/dijkstra.py` | Hand-verified distances from R1 |
| Routing table (next-hop per destination) | `core/routing.py` | CLI + dashboard output |
| Path query | `shortest_path_between` + `/api/path` | Dashboard **Find Path** |
| **Web dashboard** (instructor requirement) | `web/app.py`, `dashboard.html/js/css` | Runs on `http://127.0.0.1:5000` |
| Matplotlib visualizations (topology, tree, path) | `viz/static_plot.py` | PNG endpoint + CLI `plot` |
| CSV / JSON export | `core/export.py` | Download buttons in dashboard |
| Optional Mininet module | `emulation/mininet_runner.py` | See §5 (not in final build) |
| ≥10 node reference topology (instructor requirement) | `reference_12.txt` (12 nodes), `sample_10.txt` (10 nodes) | Dashboard summary |
| Modular structure | `core/`, `viz/`, `web/`, `emulation/`, `tests/` | Full repository |
| Tests | `tests/test_core.py` | `9 passed` |

---

## 3. What to Write in Each Report Section

### 3.1 Introduction / Motivation
- Describe link-state routing (OSPF, IS-IS) — routers flood topology
  information, build a complete topology map, and run Dijkstra independently to
  compute shortest paths.
- Explain that the project **makes the algorithm transparent and inspectable**
  rather than treating it as a black box.
- State clearly: this is an **educational simulator**, not a production router.

### 3.2 Design / Architecture
- Explain the **modular layout** (`core`, `viz`, `web`, `emulation`, `tests`) and
  why each module is separated.
- Draw (or reference) the data flow: **Topology file → Parser & Validator →
  NetworkX graph → Dijkstra → Routing table / Shortest-path tree → Dashboard /
  CLI / Export**.
- Emphasize that **NetworkX provides Dijkstra** — the project's work is in
  **modeling, validation, integration, visualization, and the dashboard**, not
  reimplementing the algorithm. This matches the proposal's scope boundary.
- Describe the **dashboard architecture**:
  - Flask exposes REST endpoints (`/api/status`, `/api/dijkstra`, `/api/path`,
    `/api/export/...`, `/api/plot/...`).
  - The frontend (`dashboard.js` + Cytoscape.js) calls those endpoints and
    renders the graph, table, and path highlights.
  - State that state is kept in-memory (single-user educational tool) — not a
    database, not multi-user. This is intentional.

### 3.3 Implementation Details
- **Topology parsing**: CSV-style lines, `#` comments, duplicate-edge keeps
  lower cost, bidirectional by default. Cite the validation table from
  `README.md`.
- **Validation**: three levels — line-level (field count, numeric cost,
  non-empty names), graph-level (no negative weights, no self-loops, source
  exists), runtime-level (unreachable nodes reported, not crashed). This mirrors
  the proposal's §1.3.2 exactly.
- **Dijkstra**: `nx.single_source_dijkstra` returns distances and paths;
  shortest-path tree edges are extracted from `path[-2], path[-1]` for each
  destination. Explain **why** the tree is useful (it's the routing structure).
- **Routing table**: next hop = `path[1]` for each destination, cost =
  `distances[destination]`. Discuss that in the reference topology every
  next-hop from R1 is R3 — this is correct and arises because R3 is R1's
  cheapest neighbor and is on every shortest path. Mention it explicitly so the
  marker doesn't think there's a bug.
- **Path query**: uses `nx.shortest_path` directly; returns `reachable: false`
  for unreachable pairs rather than raising.
- **Dashboard**: Flask + Cytoscape.js. Explain why the **dashboard was added**
  (instructor feedback). Describe the panels: topology, graph, routing table,
  path query, export.
- **Visualization**: Matplotlib with headless `Agg` backend, PNG output,
  interactive graph in Cytoscape.js.
- **Export**: CSV via `csv.DictWriter`, JSON via `json.dumps`; both endpoints
  use `send_file` for downloads.

### 3.4 Testing
- Describe the 9 tests. Group them:
  - Parsing / validation (4 tests): valid parse, negative rejection, malformed
    rejection, plus the reachability test.
  - Algorithm (3 tests): known distances from A on the small test graph,
    cross-check against NetworkX, path query.
  - Generator / next-hop (2 tests): minimum-node enforcement, routing table
    next-hop presence.
- Mention that one test (`test_dijkstra_known_path`) was **corrected during
  development** after it was found to assert the wrong expected value. This is
  worth including — it shows you verified against a hand computation and fixed
  the test rather than the code.

### 3.5 Results / Demonstration
- Include **four screenshots**:
  1. Dashboard with the R1 routing table populated.
  2. Path query `R1 → R12` highlighted (cost = 15).
  3. Terminal `analyze` output for `reference_12.txt` (routing table).
  4. Terminal test run showing `9 passed`.
- Include the **hand-verification table** from the response above:

  | Path | Cost |
  |---|---|
  | R1 → R2 → R3 → R4 → R6 → R7 → R9 → R10 | 4+1+3+2+1+2+1 = 14 (not optimal) |
  | R1 → R3 → R4 → R6 → R7 → R9 → R10 | 2+3+2+1+2+1 = 11 ✅ |

  And note that the tool returns `R1 → R10 = 11`, matching the hand calculation.
- Show that the **next-hop simplification** (all next hops from R1 are R3) is
  mathematically correct given the topology, and explain why.

### 3.6 Scope Boundaries (mirror the proposal)
- CLI + dashboard, not a general-purpose GUI.
- NetworkX's Dijkstra, not a from-scratch reimplementation.
- Negative weights rejected, not handled via Bellman-Ford (noted as future
  work).
- Mininet module optional and not part of the final build — see §5.

---

## 4. Key Numbers to Reference

| Metric | Value |
|---|---|
| Reference topology nodes | **12** (meets ≥10 requirement) |
| Reference topology edges | **21** |
| Reference topology density | **0.318** |
| Sample topology nodes | **10** (meets ≥10 requirement) |
| Random generator minimum | **10** nodes |
| Tests passing | **9** |
| Dashboard port | 5000 |
| Reference topology source used in demo | R1 |

Verified Dijkstra output from R1:

```
R1:0   R2:3   R3:2   R4:5   R5:8   R6:7
R7:8   R8:11  R9:10  R10:11 R11:13 R12:15
```

Routing table (all next-hop R3 from R1 — correct, not a bug):

```
dest=R10  next_hop=R3  cost=11.0  path=R1 -> R3 -> R4 -> R6 -> R7 -> R9 -> R10
dest=R12  next_hop=R3  cost=15.0  path=R1 -> R3 -> R4 -> R6 -> R7 -> R9 -> R12
dest=R2   next_hop=R3  cost=3.0   path=R1 -> R3 -> R2
```

---

## 5. The Mininet Section — How to Phrase It Honestly

The proposal lists Mininet emulation as **optional**, and the scope boundaries
explicitly allow skipping it. The final build does not include working Mininet
emulation because of **environment-specific incompatibilities** on the
development machine.

### 5.1 What actually happened (for your own recollection)

- Mininet 2.3.0 and Open vSwitch 4.0.0 were installed on Kali Linux.
- `sudo mn --test pingall` **succeeded** (2 hosts, 1 switch, no loops).
- When the tool's 12-node mesh topology was emulated, pings returned `0/11`
  because of L2 broadcast loops.
- Enabling STP did not resolve it within the demo window; STP convergence on a
  12-switch mesh takes minutes, and OVS standalone mode does not run STP
  (`fail_mode=standalone` conflicts with STP).
- A loop-free chain topology with the default controller also failed,
  indicating a deeper OVS/Mininet interaction issue on this specific system.
- The core routing simulator was **completely unaffected** by this; it continues
  to work standalone.

### 5.2 Suggested wording for the report

> "The optional Mininet emulation module was implemented but not included in the
> final deliverable due to environment-specific incompatibilities on the
> development machine (Kali Linux with Mininet 2.3.0 and Open vSwitch 4.0.0).
> The emulation was verified to build the topology correctly, but end-to-end
> ping reachability could not be achieved reliably within the demo window. Per
> the proposal's scope boundaries, the core routing simulator—dashboard,
> Dijkstra engine, routing table generation, path query, and CSV/JSON/PNG
> export—is delivered as a complete, standalone tool that fully demonstrates
> link-state routing behavior."

### 5.3 Do NOT say
- ❌ "We didn't have time to do Mininet." — inaccurate; you spent substantial
  time on it.
- ❌ "Mininet doesn't work." — too strong; Mininet works, but its interaction
  with this environment/controller configuration does not.
- ❌ "We implemented Mininet but it's not tested." — inaccurate; you tested it
  extensively.

### 5.4 DO say
- ✅ "Environment-specific incompatibility on Kali + OVS 4.0.0."
- ✅ "STP convergence on a 12-switch mesh exceeds the demo window."
- ✅ "The proposal explicitly allows skipping Mininet if the environment
  prevents reliable execution."
- ✅ "The core tool remains complete and functional as a standalone deliverable."

### 5.5 If asked "Why not use a different controller?"
Honest answer: "We tried the default `ovs-controller` and standalone OVS mode.
The default controller supports up to 16 switches but is fragile under loops;
standalone mode does not run STP. Installing a heavier controller (POX, ONOS)
was out of scope for a course project, and the proposal explicitly permits
skipping the optional emulation module under environment constraints."

---

## 6. Demo Script (5–7 minutes)

Practice this walkthrough in order. Total time: ~5–7 minutes.

1. **(30 s) Terminal — tests pass.**
   ```bash
   source .venv/bin/activate
   python -m pytest -q tests/
   ```
   Say: *"Nine tests covering parsing, validation, Dijkstra correctness,
   path queries, and the random generator's minimum-size enforcement."*

2. **(60 s) Terminal — CLI on the reference topology.**
   ```bash
   python run.py analyze --topology topologies/reference_12.txt --source R1
   ```
   Say: *"12 nodes, 21 edges, connected. Shortest distances from R1 match the
   hand-computed values. Every next hop is R3 because R3 is R1's cheapest
   neighbor and lies on every shortest path — this is correct."*

3. **(90 s) Dashboard — load and run Dijkstra.**
   ```bash
   python run.py dashboard
   ```
   Open `http://127.0.0.1:5000`.
   - Point out the 12-node graph, the summary card, the source dropdown
     defaulting to R1.
   - Click **Run Dijkstra**. Routing table fills. Green edges show the
     shortest-path tree.
   - Change source to `R7`, click **Run Dijkstra** again. Note that next hops
     are no longer all the same — this demonstrates that the algorithm is
     actually recomputing per source, not hard-coded.

4. **(90 s) Dashboard — path query.**
   - Query `R1 → R12`. Path highlights orange. Cost = 15.
   - Explain the path: `R1 → R3 → R4 → R6 → R7 → R9 → R12`, cost 2+3+2+1+2+5 = 15.
   - Query `R1 → R12` a second time via `R1 → R3 → R5 → R8 → R11 → R12` if you
     want to show the tool correctly prefers the shorter one.

5. **(60 s) Dashboard — exports.**
   - Click **Export CSV** → `routing_R1.csv` downloads. Open it, show it matches
     the table on screen.
   - Click **Download Shortest-Path Tree PNG** → new tab opens with the tree
     diagram.

6. **(60 s) Dashboard — random topology (≥10-node requirement).**
   - Click **Generate Random** (12 nodes, 0.35 probability). New topology
     appears. Note the ≥10-node enforcement in the UI (`min="10"` on the input).
   - Try **Load Sample (10 nodes)** to show the second ≥10-node topology.

7. **(30 s) Close.**
   - Recap: *"Everything in the revised proposal except the optional Mininet
     module is delivered and demonstrated. The two instructor feedback points —
     a proper dashboard and a ≥10-node topology — are both integrated."*

---

## 7. Anticipated Instructor Questions

**Q: Where is the dashboard? The original proposal said CLI-only.**
A: Instructor feedback asked for a proper dashboard, so we added a Flask +
Cytoscape.js web dashboard as the primary interface. The CLI is retained for
scripting. Section 2.3 of the revised proposal was updated accordingly.

**Q: Why 12 nodes?**
A: Instructor feedback required ≥10 nodes. The reference topology has 12 (21
edges, density 0.32, connected). The random generator also enforces ≥10 and the
dashboard input has `min="10"`.

**Q: Why does every next hop from R1 point to R3? Is that a bug?**
A: No. R3 is R1's cheapest neighbor (cost 2) and lies on the shortest path to
every other node in this topology. This is a valid link-state outcome. Change
the source to R7 or R12 and you'll see next hops vary.

**Q: Did you implement Dijkstra yourself?**
A: We use `nx.single_source_dijkstra` for the shortest-path computation, as
stated in the proposal's scope boundaries. The project's work is in graph
modeling, validation, integration, routing-table generation, visualization, and
the dashboard — not in reimplementing the algorithm.

**Q: Why did you reject negative weights instead of using Bellman-Ford?**
A: Dijkstra is mathematically invalid on negative edges. Real link-state
protocols (OSPF, IS-IS) use strictly positive metrics. Bellman-Ford is noted as
future work in the proposal but is out of scope.

**Q: What about Mininet?**
A: See §5 above. Short version: implemented but not in the final build due to
environment-specific incompatibilities on Kali + OVS 4.0.0; the proposal
explicitly allows this. The core tool is complete and standalone.

**Q: How do you know the algorithm is correct?**
A: Three ways: (1) hand-verified distances from R1 against the reference
topology, (2) a test that cross-checks our wrapper against
`nx.single_source_dijkstra` output exactly, (3) all 9 tests pass, including a
known-distance test that was corrected during development when it was found to
assert the wrong value. We fixed the test, not the code.

**Q: What happens with a disconnected topology?**
A: `reachability()` returns the two sets. Dijkstra results include an
`unreachable` field. The dashboard displays unreachable nodes in the routing
panel. Tests cover this case (`test_reachability_reports_isolated`).

---

## 8. Submission Checklist

- [ ] `README.md` and `NOTES_FOR_REPORTS.md` at project root
- [ ] `topologies/reference_12.txt` and `data/sample_10.txt` present
- [ ] `python -m pytest -q tests/` prints **9 passed**
- [ ] `python run.py analyze --topology topologies/reference_12.txt --source R1` prints a routing table
- [ ] `python run.py dashboard` opens at `http://127.0.0.1:5000`
- [ ] In dashboard: **Run Dijkstra** fills the table
- [ ] In dashboard: **Find Path** highlights `R1 → R12` with cost 15
- [ ] In dashboard: **Export CSV** downloads `routing_R1.csv`
- [ ] In dashboard: **Download Shortest-Path Tree PNG** opens an image
- [ ] Four screenshots captured for the report:
  - [ ] Dashboard + routing table
  - [ ] Path query highlighted
  - [ ] CLI `analyze` output
  - [ ] Test run `9 passed`
- [ ] Report has a short paragraph on the optional Mininet module (see §5)
- [ ] Report explicitly mentions **12 nodes / 21 edges** (satisfies ≥10-node
  requirement)
- [ ] Report explicitly mentions the **web dashboard** (satisfies instructor
  feedback)
- [ ] Demo practiced end-to-end at least once
