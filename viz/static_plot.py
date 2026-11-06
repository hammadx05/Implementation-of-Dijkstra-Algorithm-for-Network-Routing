"""Matplotlib visualizations: full topology, shortest-path tree, highlighted path."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend; safe inside Flask
import matplotlib.pyplot as plt
import networkx as nx


def _layout(graph: nx.Graph, seed: int = 7):
    return nx.spring_layout(graph, seed=seed, k=0.9, iterations=100)


def plot_topology(graph: nx.Graph, title: str = "Network Topology",
                  out_path: str | Path | None = None) -> bytes:
    fig, ax = plt.subplots(figsize=(10, 7))
    pos = _layout(graph)
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_color="#4C72B0",
                           node_size=900, edgecolors="white")
    nx.draw_networkx_labels(graph, pos, ax=ax, font_color="white",
                            font_size=9, font_weight="bold")
    nx.draw_networkx_edges(graph, pos, ax=ax, width=2, edge_color="#888888")
    labels = {(u, v): f"{d['weight']:.0f}" for u, v, d in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels, ax=ax, font_size=8)
    ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()
    return _finish(fig, out_path)


def plot_shortest_path_tree(graph: nx.Graph, result: dict,
                            title: str | None = None,
                            out_path: str | Path | None = None) -> bytes:
    fig, ax = plt.subplots(figsize=(10, 7))
    pos = _layout(graph)
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_color="#DDDDDD",
                           node_size=900, edgecolors="white")
    source = result["source"]
    nx.draw_networkx_nodes(graph, pos, nodelist=[source], ax=ax,
                           node_color="#C44E52", node_size=1100, edgecolors="white")
    nx.draw_networkx_labels(graph, pos, ax=ax, font_size=9, font_weight="bold")
    nx.draw_networkx_edges(graph, pos, ax=ax, width=1, edge_color="#CCCCCC")
    nx.draw_networkx_edges(graph, pos, edgelist=result["tree_edges"], ax=ax,
                           width=3, edge_color="#55A868")
    labels = {(u, v): f"{d['weight']:.0f}" for u, v, d in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels, ax=ax, font_size=8)
    ax.set_title(title or f"Shortest-Path Tree from {source}")
    ax.axis("off")
    fig.tight_layout()
    return _finish(fig, out_path)


def plot_highlighted_path(graph: nx.Graph, path: list[str], source: str,
                          destination: str, cost: float,
                          out_path: str | Path | None = None) -> bytes:
    fig, ax = plt.subplots(figsize=(10, 7))
    pos = _layout(graph)
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_color="#DDDDDD",
                           node_size=900, edgecolors="white")
    nx.draw_networkx_nodes(graph, pos, nodelist=[source], ax=ax,
                           node_color="#C44E52", node_size=1100, edgecolors="white")
    nx.draw_networkx_nodes(graph, pos, nodelist=[destination], ax=ax,
                           node_color="#8172B2", node_size=1100, edgecolors="white")
    nx.draw_networkx_labels(graph, pos, ax=ax, font_size=9, font_weight="bold")
    nx.draw_networkx_edges(graph, pos, ax=ax, width=1, edge_color="#CCCCCC")
    path_edges = list(zip(path[:-1], path[1:]))
    nx.draw_networkx_edges(graph, pos, edgelist=path_edges, ax=ax,
                           width=4, edge_color="#DD8452")
    labels = {(u, v): f"{d['weight']:.0f}" for u, v, d in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels, ax=ax, font_size=8)
    ax.set_title(f"Path {source} -> {destination}  (cost = {cost:g})")
    ax.axis("off")
    fig.tight_layout()
    return _finish(fig, out_path)


def _finish(fig, out_path) -> bytes:
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    if out_path:
        fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return buf.getvalue()
