"""Topology parsing, validation, and random generation."""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import networkx as nx


class TopologyError(ValueError):
    """Raised when a topology input is invalid."""


MIN_RANDOM_NODES = 10


@dataclass
class ParsedTopology:
    graph: nx.Graph
    source_lines: list[str]  # raw non-empty, non-comment lines


def parse_topology_text(text: str) -> ParsedTopology:
    """Parse CSV-style lines: Node1, Node2, Cost. '#' starts a comment."""
    graph = nx.Graph()
    raw_lines: list[str] = []

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        raw_lines.append(line)

        fields = [f.strip() for f in line.split(",")]
        if len(fields) != 3:
            raise TopologyError(
                f"Line {lineno}: expected 3 fields (Node1, Node2, Cost), got {len(fields)}: {line!r}"
            )
        u, v, cost_s = fields
        if not u or not v:
            raise TopologyError(f"Line {lineno}: node names must be non-empty.")
        try:
            cost = float(cost_s)
        except ValueError:
            raise TopologyError(f"Line {lineno}: cost {cost_s!r} is not numeric.") from None
        if cost < 0:
            raise TopologyError(
                f"Line {lineno}: negative cost {cost} rejected (Dijkstra requires non-negative weights)."
            )
        if u == v:
            raise TopologyError(f"Line {lineno}: self-loop on node {u!r} is not allowed.")

        # If duplicate edge, keep the lower cost (typical link-state behavior)
        if graph.has_edge(u, v):
            if cost < graph[u][v]["weight"]:
                graph[u][v]["weight"] = cost
        else:
            graph.add_edge(u, v, weight=cost)

    if graph.number_of_nodes() == 0:
        raise TopologyError("Topology is empty: no valid links found.")
    return ParsedTopology(graph=graph, source_lines=raw_lines)


def parse_topology_file(path: str | Path) -> ParsedTopology:
    return parse_topology_text(Path(path).read_text(encoding="utf-8"))


def validate_source(graph: nx.Graph, source: str) -> None:
    if source not in graph:
        raise TopologyError(f"Source node {source!r} does not exist in topology.")


def reachability(graph: nx.Graph, source: str) -> tuple[set[str], set[str]]:
    """Return (reachable, unreachable) node sets from a source."""
    validate_source(graph, source)
    reachable = set(nx.node_connected_component(graph, source))
    unreachable = set(graph.nodes) - reachable
    return reachable, unreachable


def generate_random_topology(
    n_nodes: int = 12,
    edge_probability: float = 0.35,
    cost_min: int = 1,
    cost_max: int = 10,
    seed: int | None = None,
) -> ParsedTopology:
    """Generate a connected random topology. Enforces n_nodes >= 10."""
    if n_nodes < MIN_RANDOM_NODES:
        raise TopologyError(
            f"Random topology must have at least {MIN_RANDOM_NODES} nodes (got {n_nodes})."
        )
    if not (0 < edge_probability <= 1):
        raise TopologyError("edge_probability must be in (0, 1].")
    if cost_min < 0 or cost_max < cost_min:
        raise TopologyError("Invalid cost range.")

    rng = random.Random(seed)
    nodes = [f"N{i+1}" for i in range(n_nodes)]
    graph = nx.Graph()
    graph.add_nodes_from(nodes)

    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if rng.random() < edge_probability:
                graph.add_edge(nodes[i], nodes[j], weight=rng.randint(cost_min, cost_max))

    # Guarantee connectivity: add a random spanning tree if needed.
    if not nx.is_connected(graph):
        comps = list(nx.connected_components(graph))
        for k in range(len(comps) - 1):
            u = rng.choice(list(comps[k]))
            v = rng.choice(list(comps[k + 1]))
            graph.add_edge(u, v, weight=rng.randint(cost_min, cost_max))

    # Emit as CSV text (so it round-trips through the same parser)
    lines = []
    for u, v, data in graph.edges(data=True):
        lines.append(f"{u}, {v}, {int(data['weight'])}")
    return parse_topology_text("\n".join(lines))


def topology_to_text(graph: nx.Graph) -> str:
    lines = []
    for u, v, data in graph.edges(data=True):
        lines.append(f"{u}, {v}, {data['weight']}")
    return "\n".join(lines)


def summary(graph: nx.Graph) -> dict:
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "connected": nx.is_connected(graph) if graph.number_of_nodes() else False,
        "density": nx.density(graph) if graph.number_of_nodes() > 1 else 0.0,
        "node_list": sorted(graph.nodes()),
    }
