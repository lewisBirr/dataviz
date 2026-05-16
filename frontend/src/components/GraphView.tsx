import { useEffect, useMemo, useState } from "react";
import { CosmographProvider, Cosmograph } from "@cosmograph/react";
import type { CosmographConfig } from "@cosmograph/react";
import { loadGraph } from "@/lib/data";
import { useGraphStore } from "@/store";
import type { GraphNode } from "@/types";

// Show labels for the top N nodes by betweenness centrality.
const LABEL_TOP_N = 30;

export function GraphView() {
  const setGraphData = useGraphStore((s) => s.setGraphData);
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode);
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId);

  const [config, setConfig] = useState<CosmographConfig | null>(null);
  const [orderedNodes, setOrderedNodes] = useState<GraphNode[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadGraph()
      .then(({ orderedNodes, edges, cosmographConfig }) => {
        setOrderedNodes(orderedNodes);
        setGraphData(orderedNodes, edges);
        setConfig(cosmographConfig);
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
      });
  }, [setGraphData]);

  // Top-N node ids by betweenness — shown as labels.
  const labelNodeIds = useMemo<string[]>(() => {
    if (!orderedNodes.length) return [];
    return [...orderedNodes]
      .sort((a, b) => b.betweenness_centrality - a.betweenness_centrality)
      .slice(0, LABEL_TOP_N)
      .map((n) => n.id);
  }, [orderedNodes]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-white/60 text-sm px-8 text-center">
        <p>Failed to load graph data: {error}</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="flex items-center justify-center h-full text-white/40 text-sm">
        Loading network…
      </div>
    );
  }

  return (
    <CosmographProvider>
      <Cosmograph
        {...config}
        backgroundColor="#0D1117"
        // Labels for top nodes only
        showLabelsFor={labelNodeIds}
        // Interaction
        onPointClick={(index: number) => {
          const node = orderedNodes[index];
          if (!node) return;
          setSelectedNode(selectedNodeId === node.id ? null : node.id);
        }}
        onClick={() => setSelectedNode(null)}
        // Link appearance
        linkColor="#30363D"
        linkOpacity={0.6}
        // Simulation
        simulationGravity={0.1}
        simulationRepulsion={1.5}
        simulationLinkSpring={0.5}
        simulationFriction={0.85}
      />
    </CosmographProvider>
  );
}
