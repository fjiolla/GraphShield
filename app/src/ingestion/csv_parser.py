"""
CSV parser.

Reads edge-list CSVs (and optionally a companion nodes CSV) into
standardised node/edge records.

Expected edge CSV columns (minimum):
    source, target

Optional columns: weight, type, and any other edge attributes.

A separate nodes file can be provided via the ``nodes_path`` parameter
in the constructor.  Its minimum column is ``id``; any additional columns
become node attributes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.src.ingestion.base_parser import BaseParser, EdgeRecord, NodeRecord

logger = logging.getLogger(__name__)


class CSVParser(BaseParser):
    """Parse CSV files into standardised node/edge records."""

    def __init__(self, nodes_path: str | None = None) -> None:
        """Initialise the CSV parser.

        Args:
            nodes_path: Optional path to a separate nodes CSV file.
                        If *None*, nodes are inferred from the edges.
        """
        self._nodes_path = nodes_path

    def parse(self, source: str) -> tuple[list[NodeRecord], list[EdgeRecord]]:
        """Read a CSV edge-list file and return (nodes, edges).

        Args:
            source: Path to the edges CSV file.

        Returns:
            Tuple of node dicts and edge dicts.
        """
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        logger.info("Parsing CSV file: %s", path)

        edges = self._parse_edges(path)
        nodes = self._parse_nodes(edges)

        logger.info(
            "CSV parsed — %d nodes, %d edges", len(nodes), len(edges)
        )
        return nodes, edges

    # ── Internal helpers ─────────────────────────────────────────────

    @staticmethod
    def _parse_edges(path: Path) -> list[EdgeRecord]:
        """Load edges from a CSV file."""
        peek_df = pd.read_csv(path, nrows=0)
        peek_cols = [str(c).strip().lower() for c in peek_df.columns]

        if "source" in peek_cols and "target" in peek_cols:
            df = pd.read_csv(path)
            df.columns = [str(c).strip().lower() for c in df.columns]
        else:
            # Fallback: assume no header and use first two columns
            df = pd.read_csv(path, header=None)
            cols = list(df.columns)
            if len(cols) < 2:
                raise ValueError("Edge CSV must contain at least two columns.")
            df.rename(columns={cols[0]: "source", cols[1]: "target"}, inplace=True)
            df.columns = [str(c).strip().lower() for c in df.columns]

        edges: list[EdgeRecord] = []
        for _, row in df.iterrows():
            # Skip if row is potentially a parsed text header
            if str(row["source"]).lower() in ("source", "node1", "u", "from") \
               and str(row["target"]).lower() in ("target", "node2", "v", "to"):
                continue

            record: dict[str, Any] = {
                "source": str(row["source"]),
                "target": str(row["target"]),
            }
            # Include any extra columns as edge attributes
            for col in df.columns:
                if col not in ("source", "target") and pd.notna(row[col]):
                    record[col] = row[col]
            edges.append(record)
        return edges

    def _parse_nodes(
        self, edges: list[EdgeRecord]
    ) -> list[NodeRecord]:
        """Load nodes from a dedicated CSV, or infer from edges."""
        if self._nodes_path:
            return self._load_nodes_file(Path(self._nodes_path))

        # Infer unique node IDs from edges
        node_ids: set[str] = set()
        for e in edges:
            node_ids.add(e["source"])
            node_ids.add(e["target"])

        return [{"id": nid} for nid in sorted(node_ids)]

    @staticmethod
    def _load_nodes_file(path: Path) -> list[NodeRecord]:
        """Read a nodes CSV with at least an ``id`` column."""
        if not path.exists():
            raise FileNotFoundError(f"Nodes CSV not found: {path}")

        peek_df = pd.read_csv(path, nrows=0)
        peek_cols = [str(c).strip().lower() for c in peek_df.columns]

        if "id" in peek_cols or "node" in peek_cols:
            df = pd.read_csv(path)
            df.columns = [str(c).strip().lower() for c in df.columns]
            if "id" not in df.columns and "node" in df.columns:
                df.rename(columns={"node": "id"}, inplace=True)
        else:
            # Fallback: assume no header and use first column as ID
            df = pd.read_csv(path, header=None)
            cols = list(df.columns)
            if len(cols) < 1:
                raise ValueError("Nodes CSV must contain at least one column.")
            df.rename(columns={cols[0]: "id"}, inplace=True)
            df.columns = [str(c).strip().lower() for c in df.columns]

        nodes: list[NodeRecord] = []
        for _, row in df.iterrows():
            if str(row["id"]).lower() in ("id", "node", "n"):
                continue

            record: dict[str, Any] = {}
            for col in df.columns:
                if pd.notna(row[col]):
                    record[col] = row[col]
            record["id"] = str(record["id"])
            nodes.append(record)
        return nodes
