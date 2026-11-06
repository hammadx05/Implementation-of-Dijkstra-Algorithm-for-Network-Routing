"""Dijkstra shortest-path engine using NetworkX."""
from __future__ import annotations

import networkx as nx

from .topology import TopologyError, reachability


def run_dijkstra(graph: nx.Graph, source: str) -> dict:
    """
    Compute shortest paths from source to all reachable nodes.

    Returns:
        {
          "source": str,
          "distances": {node: float},
          "paths": {node: [node, ...]},       # shortest path (list of nodes)
          "tree_edges": [(u, v), ...],        # edges of shortest-path tree
          "unreachable": [node, ...],
        }
    """
    reachable, unreachable = reachability(graph, source)

    # nx.single_source_dijkstra returns (distances, paths)
    distances, paths = nx.single_source_dijkstra(graph, source, weight="weight")

    # Build shortest-path tree edges
    tree_edges = []
    for dest, path in paths.items():
        if dest == source:
            continue
        # tree edge is the last hop into `dest` on its shortest path
        tree_edges.append((path[-2], dest))

    return {
        "source": source,
        "distances": dict(distances),
        "paths": dict(paths),
        "tree_edges": tree_edges,
        "unreachable": sorted(unreachable),
    }


def shortest_path_between(graph: nx.Graph, source: str, destination: str) -> dict:
    """Return the shortest path and cost between two specific nodes."""
    if source not in graph:
        raise TopologyError(f"Source node {source!r} does not exist.")
    if destination not in graph:
        raise TopologyError(f"Destination node {destination!r} does not exist.")
    try:
        path = nx.shortest_path(graph, source, destination, weight="weight")
        cost = nx.shortest_path_length(graph, source, destination, weight="weight")
    except nx.NetworkXNoPath:
        return {"source": source, "destination": destination,
                "reachable": False, "path": [], "cost": None}
    return {
        "source": source,
        "destination": destination,
        "reachable": True,
        "path": path,
        "cost": cost,
    }
