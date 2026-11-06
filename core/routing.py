"""Routing table generation from a Dijkstra result."""
from __future__ import annotations

from .dijkstra import run_dijkstra


def build_routing_table(graph, source: str) -> list[dict]:
    """
    Produce a next-hop forwarding table.

    Each row: {destination, next_hop, cost, path}
    """
    result = run_dijkstra(graph, source)
    rows = []
    for dest, path in result["paths"].items():
        if dest == source:
            continue
        next_hop = path[1] if len(path) > 1 else dest
        rows.append({
            "destination": dest,
            "next_hop": next_hop,
            "cost": result["distances"][dest],
            "path": path,
        })
    rows.sort(key=lambda r: r["destination"])
    return rows
