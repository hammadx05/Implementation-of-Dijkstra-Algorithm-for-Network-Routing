"""Entry point: run the dashboard or use the CLI."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.dijkstra import run_dijkstra, shortest_path_between
from core.export import routing_table_to_csv, routing_table_to_json
from core.routing import build_routing_table
from core.topology import (
    TopologyError,
    generate_random_topology,
    parse_topology_file,
    summary,
    topology_to_text,
)
from viz.static_plot import (
    plot_highlighted_path,
    plot_shortest_path_tree,
    plot_topology,
)


def cmd_dashboard(args):
    from web.app import main as web_main
    web_main(host=args.host, port=args.port, debug=args.debug)


def cmd_analyze(args):
    graph = _load_graph(args)
    print("Topology summary:", summary(graph))
    result = run_dijkstra(graph, args.source)
    print(f"\nShortest distances from {args.source}:")
    for node, dist in sorted(result["distances"].items()):
        print(f"  {node:<6} {dist}")
    if result["unreachable"]:
        print("Unreachable:", ", ".join(result["unreachable"]))
    print("\nRouting table:")
    for row in build_routing_table(graph, args.source):
        print(f"  dest={row['destination']:<6} next_hop={row['next_hop']:<6} "
              f"cost={row['cost']:<6} path={' -> '.join(row['path'])}")
    if args.export:
        suffix = Path(args.export).suffix.lower()
        if suffix == ".csv":
            text = routing_table_to_csv(build_routing_table(graph, args.source))
        else:
            text = routing_table_to_json(build_routing_table(graph, args.source))
        Path(args.export).write_text(text)
        print(f"\nRouting table exported to {args.export}")


def cmd_path(args):
    graph = _load_graph(args)
    result = shortest_path_between(graph, args.source, args.destination)
    if not result["reachable"]:
        print(f"No path from {args.source} to {args.destination}.")
        sys.exit(1)
    print(f"Path: {' -> '.join(result['path'])}")
    print(f"Cost: {result['cost']}")


def cmd_random(args):
    parsed = generate_random_topology(
        n_nodes=args.nodes, edge_probability=args.prob, seed=args.seed
    )
    print(topology_to_text(parsed.graph))
    if args.out:
        Path(args.out).write_text(topology_to_text(parsed.graph))
        print(f"\nSaved to {args.out}", file=sys.stderr)


def cmd_plot(args):
    graph = _load_graph(args)
    if args.kind == "topology":
        plot_topology(graph, out_path=args.out)
    elif args.kind == "tree":
        result = run_dijkstra(graph, args.source)
        plot_shortest_path_tree(graph, result, out_path=args.out)
    elif args.kind == "path":
        result = shortest_path_between(graph, args.source, args.destination)
        if not result["reachable"]:
            print("No path.", file=sys.stderr); sys.exit(1)
        plot_highlighted_path(graph, result["path"], args.source, args.destination,
                              result["cost"], out_path=args.out)
    print(f"Saved {args.out}")


def cmd_mininet(args):
    from emulation.mininet_runner import MininetUnavailable, verify_connectivity
    graph = _load_graph(args)
    try:
        results = verify_connectivity(graph, args.source, list(graph.nodes))
    except MininetUnavailable as e:
        print(f"Mininet unavailable: {e}", file=sys.stderr); sys.exit(2)
    for dest, r in results.items():
        print(f"{args.source} -> {dest}: {'OK' if r['reachable'] else 'FAIL'}")


def _load_graph(args):
    if args.random:
        return generate_random_topology(
            n_nodes=args.nodes, edge_probability=args.prob, seed=args.seed
        ).graph
    if not args.topology:
        raise SystemExit("--topology is required (or use --random).")
    return parse_topology_file(args.topology).graph


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="NPS Dijkstra Routing Tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dashboard", help="Run the web dashboard")
    d.add_argument("--host", default="127.0.0.1")
    d.add_argument("--port", type=int, default=5000)
    d.add_argument("--debug", action="store_true")
    d.set_defaults(func=cmd_dashboard)

    a = sub.add_parser("analyze", help="Run Dijkstra & print routing table")
    _add_common(a)
    a.add_argument("--source", required=True)
    a.add_argument("--export", help="Export routing table to CSV or JSON")
    a.set_defaults(func=cmd_analyze)

    pa = sub.add_parser("path", help="Query shortest path between two nodes")
    _add_common(pa)
    pa.add_argument("--source", required=True)
    pa.add_argument("--destination", required=True)
    pa.set_defaults(func=cmd_path)

    r = sub.add_parser("random", help="Generate a random topology")
    r.add_argument("--nodes", type=int, default=12)
    r.add_argument("--prob", type=float, default=0.35)
    r.add_argument("--seed", type=int, default=None)
    r.add_argument("--out")
    r.set_defaults(func=cmd_random)

    pl = sub.add_parser("plot", help="Render static PNG plot")
    _add_common(pl)
    pl.add_argument("--kind", choices=["topology", "tree", "path"], required=True)
    pl.add_argument("--source")
    pl.add_argument("--destination")
    pl.add_argument("--out", default="plot.png")
    pl.set_defaults(func=cmd_plot)

    m = sub.add_parser("mininet", help="Optional Mininet connectivity check")
    _add_common(m)
    m.add_argument("--source", required=True)
    m.set_defaults(func=cmd_mininet)
    return p


def _add_common(p):
    p.add_argument("--topology")
    p.add_argument("--random", action="store_true")
    p.add_argument("--nodes", type=int, default=12)
    p.add_argument("--prob", type=float, default=0.35)
    p.add_argument("--seed", type=int, default=None)


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except TopologyError as e:
        print(f"Topology error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
