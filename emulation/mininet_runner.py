"""
Optional Mininet emulation. If Mininet (or root privileges) is unavailable,
functions raise MininetUnavailable so the core tool still works.
"""
from __future__ import annotations

import subprocess
from typing import Iterable

try:  # Mininet is only importable when installed & run as root
    from mininet.net import Mininet
    from mininet.node import OVSKernelSwitch, Controller
    from mininet.link import TCLink
    _MININET_OK = True
except Exception:  # pragma: no cover
    _MININET_OK = False


class MininetUnavailable(RuntimeError):
    pass


def is_available() -> bool:
    return _MININET_OK


def verify_connectivity(graph, source: str, destinations: Iterable[str],
                        ping_count: int = 1) -> dict:
    """
    Emulate the topology, apply routing (via static routes), and verify
    reachability with ping. Returns per-destination results.
    """
    if not _MININET_OK:
        raise MininetUnavailable(
            "Mininet is not installed or not importable. Install Mininet and run as root."
        )
    # Import here so module can be safely imported without mininet
    from mininet.net import Mininet
    from mininet.node import OVSKernelSwitch, Controller
    from mininet.link import TCLink

    net = Mininet(controller=Controller, switch=OVSKernelSwitch, link=TCLink)
    net.addController("c0")

    nodes = {name: net.addHost(name) for name in graph.nodes}
    # Create a switch per host to avoid name collisions
    switches = {name: net.addSwitch(f"s_{name}") for name in graph.nodes}
    for name in graph.nodes:
        net.addLink(nodes[name], switches[name])
    for u, v, data in graph.edges(data=True):
        net.addLink(switches[u], switches[v], bw=max(1, int(data["weight"])))

    net.start()
    results = {}
    try:
        src_host = nodes[source]
        for dest in destinations:
            if dest == source:
                continue
            dst_host = nodes[dest]
            out = src_host.cmd(f"ping -c {ping_count} -W 1 {dst_host.IP()}")
            results[dest] = {
                "reachable": " 0% packet loss" in out or " 1 received" in out
                or "1 packets transmitted, 1 received" in out,
                "raw": out,
            }
    finally:
        net.stop()
    return results


def run_ping_test(topology_path: str, source: str, destination: str) -> str:
    """CLI helper: run a single ping test and return output."""
    cmd = ["python", "-c", "import sys; sys.exit(0)"]  # placeholder
    # Actual use: call verify_connectivity with a parsed graph.
    raise NotImplementedError(
        "Use verify_connectivity(graph, source, [destination]) instead."
    )
