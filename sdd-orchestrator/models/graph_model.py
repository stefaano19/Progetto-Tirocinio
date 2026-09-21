"""Graph Model — Knowledge graph loading and HTML visualization generation.

Reads the ``graphify-out/graph.json`` artifact (produced by the `graphify`
skill — see `graphify-out/GRAPH_REPORT.md` for the human-readable summary)
and prepares data for the graph view (§5.9 of claude.md — RF8/RF9).

Node/edge shape produced by graphify (see `~/.claude/skills/graphify`):
  node:  {"id", "label", "file_type", "source_file", "source_location",
          "community", "community_name", ...}
  edge:  {"source", "target", "relation", "confidence", "confidence_score",
          "source_file", "source_location", "weight"}

ZERO PySide6 dependencies — pure Python (rule §10.1). Reading graph.json can
be slow for very large graphs, so callers SHOULD run ``load_graph()`` in a
QThread when wiring this into the UI (rule §10.3), the same way
``codebase_model.py`` is wrapped by ``codebase_worker.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from utils.paths import GRAPHIFY_GRAPH_FILE


class GraphModel:
    """Loads and prepares the knowledge graph produced by `graphify`.

    Keeps the last-loaded graph in memory (nodes indexed by id, plus the
    raw edge list) so ``get_node_details()`` can resolve backlinks/outgoing
    edges without re-reading/re-parsing the JSON file on every call.
    """

    def __init__(self) -> None:
        self._nodes_by_id: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []

    def graph_exists(self, workspace: str) -> bool:
        """Checks whether ``graphify-out/graph.json`` exists in *workspace*."""
        return (Path(workspace) / GRAPHIFY_GRAPH_FILE).is_file()

    def load_graph(self, workspace: str) -> dict[str, Any] | None:
        """Loads ``graphify-out/graph.json``, or ``None`` if missing/invalid.

        As a side effect, caches nodes (indexed by id) and edges internally
        so a subsequent ``get_node_details()`` call can resolve backlinks
        and outgoing edges for the graph that was just loaded.
        """
        graph_path = Path(workspace) / GRAPHIFY_GRAPH_FILE
        if not graph_path.is_file():
            self._nodes_by_id = {}
            self._edges = []
            return None

        try:
            data = json.loads(graph_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._nodes_by_id = {}
            self._edges = []
            return None

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        self._nodes_by_id = {node["id"]: node for node in nodes if "id" in node}
        self._edges = edges

        return data

    def get_node_details(self, node_id: str) -> dict[str, Any]:
        """Returns a node's attributes plus resolved backlinks/outgoing edges.

        Must be called after ``load_graph()`` has populated the internal
        cache for the workspace of interest. Returns ``{}`` for an unknown
        node id (e.g. stale selection after the graph changed).
        """
        node = self._nodes_by_id.get(node_id)
        if node is None:
            return {}

        outgoing = [
            {
                "node_id": edge.get("target"),
                "label": self._nodes_by_id.get(edge.get("target"), {}).get("label", edge.get("target")),
                "relation": edge.get("relation"),
                "confidence": edge.get("confidence"),
            }
            for edge in self._edges
            if edge.get("source") == node_id
        ]
        backlinks = [
            {
                "node_id": edge.get("source"),
                "label": self._nodes_by_id.get(edge.get("source"), {}).get("label", edge.get("source")),
                "relation": edge.get("relation"),
                "confidence": edge.get("confidence"),
            }
            for edge in self._edges
            if edge.get("target") == node_id
        ]

        return {
            **node,
            "outgoing": outgoing,
            "backlinks": backlinks,
        }

    def generate_html_visualization(self, graph_data: dict[str, Any] | None) -> str:
        """Builds a self-contained HTML page rendering *graph_data*.

        Uses Graphology + Sigma.js (loaded from a CDN) with a ForceAtlas2
        layout, community-based node coloring, a text search box, and
        pan/zoom/hover/click interaction — meant to be loaded into a
        ``QWebEngineView`` (``graph_view.py``, Step 5.1.2). Requires
        network access for the CDN scripts, same approach LLM Wiki takes
        with its bundled Sigma.js frontend (§3.1/§5.9 of claude.md).

        A window-level hook, ``window.onGraphNodeClick(nodeId)``, is called
        on every node click; the Qt side can inject a replacement via
        ``QWebEnginePage.runJavaScript()`` (or a ``QWebChannel``) to route
        selections to the native details panel. Until that hook is
        overridden, clicking a node shows its details in an inline panel so
        the page is fully functional on its own (e.g. opened in a browser).
        """
        nodes = (graph_data or {}).get("nodes", [])
        edges = (graph_data or {}).get("edges", [])

        graph_json = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False)

        return _HTML_TEMPLATE.replace("__GRAPH_DATA__", graph_json)


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>Knowledge Graph</title>
<script src="https://cdn.jsdelivr.net/npm/graphology@0.25.4/dist/graphology.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/graphology-layout-forceatlas2@0.10.1/dist/graphology-layout-forceatlas2.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/sigma@2.4.0/dist/sigma.min.js"></script>
<style>
  html, body { margin: 0; padding: 0; height: 100%; background: #1a1b1e; overflow: hidden; }
  #graph-container { position: absolute; inset: 0; }
  #search-box {
    position: absolute; top: 12px; left: 12px; z-index: 10;
    width: 220px; padding: 8px 10px; border-radius: 6px; border: 1px solid #373a40;
    background: #25262b; color: #f8f9fa; font: 13px -apple-system, sans-serif;
  }
  #details-panel {
    position: absolute; top: 12px; right: 12px; z-index: 10;
    width: 280px; max-height: calc(100% - 24px); overflow-y: auto;
    background: #25262b; border: 1px solid #373a40; border-radius: 8px;
    padding: 12px 14px; color: #f8f9fa; font: 13px -apple-system, sans-serif;
    display: none;
  }
  #details-panel h3 { margin: 0 0 6px 0; font-size: 14px; color: #f8f9fa; }
  #details-panel .meta { color: #909296; margin-bottom: 10px; }
  #details-panel .section-title { color: #909296; text-transform: uppercase; font-size: 11px; margin: 10px 0 4px; }
  #details-panel ul { margin: 0; padding-left: 16px; }
  #empty-state {
    position: absolute; inset: 0; display: none; align-items: center; justify-content: center;
    color: #909296; font: 14px -apple-system, sans-serif;
  }
</style>
</head>
<body>
  <input id="search-box" type="text" placeholder="Search nodes..." />
  <div id="graph-container"></div>
  <div id="details-panel"></div>
  <div id="empty-state">Graph data not found.</div>

  <script>
    const graphData = __GRAPH_DATA__;

    // Fallback details renderer — overridden by the Qt side via
    // window.onGraphNodeClick when a QWebChannel bridge is wired up.
    window.onGraphNodeClick = function (nodeId, attrs) {
      const panel = document.getElementById("details-panel");
      if (!attrs) { panel.style.display = "none"; return; }
      panel.style.display = "block";
      panel.innerHTML =
        "<h3>" + (attrs.label || nodeId) + "</h3>" +
        "<div class='meta'>" + (attrs.file_type || "") +
          (attrs.community_name ? " &middot; " + attrs.community_name : "") + "</div>" +
        (attrs.source_file ? "<div class='meta'>" + attrs.source_file + "</div>" : "");
    };

    if (!graphData.nodes || graphData.nodes.length === 0) {
      document.getElementById("empty-state").style.display = "flex";
    } else {
      const graph = new graphology.Graph({ multi: true });

      // Deterministic color per community so repeated views stay stable.
      const communityColors = {};
      function colorFor(community) {
        const key = community === undefined || community === null ? "_none" : String(community);
        if (!communityColors[key]) {
          let hash = 0;
          for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) >>> 0;
          communityColors[key] = "hsl(" + (hash % 360) + ", 65%, 60%)";
        }
        return communityColors[key];
      }

      graphData.nodes.forEach((n) => {
        if (graph.hasNode(n.id)) return;
        graph.addNode(n.id, {
          label: n.label || n.id,
          size: 4,
          color: colorFor(n.community),
          x: Math.random(),
          y: Math.random(),
          ...n,
        });
      });

      graphData.edges.forEach((e) => {
        if (!graph.hasNode(e.source) || !graph.hasNode(e.target)) return;
        try {
          graph.addEdge(e.source, e.target, {
            label: e.relation || "",
            size: Math.max(0.5, (e.weight || 1) * 0.5),
            color: "#373a40",
          });
        } catch (err) { /* duplicate edge in multi-graph, ignore */ }
      });

      // Bounded synchronous layout — good enough for the graph sizes
      // graphify typically produces; a WebWorker-based incremental layout
      // (like LLM Wiki's) can replace this later if graphs get huge.
      graphologyLibrary.layoutForceAtlas2.assign(graph, { iterations: 150 });

      const renderer = new Sigma(graph, document.getElementById("graph-container"), {
        renderEdgeLabels: false,
        defaultNodeColor: "#909296",
      });

      let selectedNode = null;

      renderer.on("clickNode", ({ node }) => {
        selectedNode = node;
        window.onGraphNodeClick(node, graph.getNodeAttributes(node));
        renderer.refresh();
      });

      renderer.on("clickStage", () => {
        selectedNode = null;
        window.onGraphNodeClick(null, null);
        renderer.refresh();
      });

      renderer.setSetting("nodeReducer", (node, data) => {
        const res = { ...data };
        if (selectedNode && node !== selectedNode && !graph.areNeighbors(node, selectedNode)) {
          res.color = "#373a40";
        }
        return res;
      });

      document.getElementById("search-box").addEventListener("input", (ev) => {
        const query = ev.target.value.trim().toLowerCase();
        if (!query) {
          selectedNode = null;
          renderer.refresh();
          return;
        }
        const match = graph.nodes().find((n) => {
          const label = (graph.getNodeAttribute(n, "label") || "").toLowerCase();
          return label.includes(query);
        });
        if (match) {
          selectedNode = match;
          window.onGraphNodeClick(match, graph.getNodeAttributes(match));
          renderer.refresh();
        }
      });
    }
  </script>
</body>
</html>
"""
