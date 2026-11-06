"""Export routing tables and path results to CSV or JSON."""
from __future__ import annotations

import csv
import io
import json


def routing_table_to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["destination", "next_hop", "cost", "path"])
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, "path": "->".join(row["path"])})
    return buf.getvalue()


def routing_table_to_json(rows: list[dict]) -> str:
    return json.dumps(rows, indent=2)


def dijkstra_result_to_json(result: dict) -> str:
    # distances keys are strings; everything JSON-serializable
    return json.dumps(result, indent=2)
