"""Minimal smoke tests for the core logic."""
from core.dijkstra import run_dijkstra, shortest_path_between
from core.routing import build_routing_table
from core.topology import (
    TopologyError,
    generate_random_topology,
    parse_topology_text,
    reachability,
    summary,
)

TEXT = """\
# sample
A, B, 4
A, C, 2
B, C, 1
B, D, 5
C, D, 8
D, E, 2
D, F, 6
E, F, 3
"""


def test_parse_valid():
    parsed = parse_topology_text(TEXT)
    assert parsed.graph.number_of_nodes() == 6
    assert parsed.graph.number_of_edges() == 8


def test_reject_negative():
    try:
        parse_topology_text("A, B, -1")
    except TopologyError:
        return
    raise AssertionError("expected TopologyError")


def test_reject_malformed():
    try:
        parse_topology_text("A, B")
    except TopologyError:
        return
    raise AssertionError("expected TopologyError")

def test_dijkstra_known_path():
    g = parse_topology_text(TEXT).graph
    r = run_dijkstra(g, "A")

    # Hand-computed shortest distances from A on the test topology.
    # A->B=4, A->C=2, A->C->B->D=8, A->C->B->D->E=10, A->C->B->D->F=14 (or via E: 13)
    expected = {
        "A": 0.0,
        "B": 3.0,   # A->C->B (2+1) beats A->B (4)
        "C": 2.0,
        "D": 8.0,   # A->C->B->D (2+1+5) beats A->B->D (9) and A->C->D (10)
        "E": 10.0,  # A->C->B->D->E (2+1+5+2)
        "F": 13.0,  # A->C->B->D->E->F (2+1+5+2+3) beats D->F (8+6=14)
    }
    for node, dist in expected.items():
        assert r["distances"][node] == dist, (
            f"{node}: expected {dist}, got {r['distances'][node]}"
        )

    # Sanity-check the actual path to E is what we think it is.
    assert r["paths"]["E"] == ["A", "C", "B", "D", "E"]


def test_dijkstra_known_path_matches_networkx():
    """Cross-check: our output must match nx.single_source_dijkstra exactly."""
    import networkx as nx
    g = parse_topology_text(TEXT).graph
    ours = run_dijkstra(g, "A")
    ref_dist, ref_paths = nx.single_source_dijkstra(g, "A", weight="weight")
    assert ours["distances"] == ref_dist
    assert ours["paths"] == ref_paths

def test_path_query():
    g = parse_topology_text(TEXT).graph
    r = shortest_path_between(g, "A", "F")
    assert r["reachable"]
    assert r["path"][0] == "A" and r["path"][-1] == "F"


def test_routing_table_has_next_hops():
    g = parse_topology_text(TEXT).graph
    rows = build_routing_table(g, "A")
    assert all("next_hop" in row for row in rows)
    assert rows and rows[0]["next_hop"] != "A"


def test_random_min_nodes():
    try:
        generate_random_topology(n_nodes=5)
    except TopologyError:
        pass
    else:
        raise AssertionError("expected TopologyError")
    parsed = generate_random_topology(n_nodes=10, edge_probability=0.5, seed=1)
    assert parsed.graph.number_of_nodes() == 10
    assert summary(parsed.graph)["connected"]


def test_reachability_reports_isolated():
    g = parse_topology_text("A, B, 1\nC, D, 1").graph
    reachable, unreachable = reachability(g, "A")
    assert reachable == {"A", "B"}
    assert unreachable == {"C", "D"}
