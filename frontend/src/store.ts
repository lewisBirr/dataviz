import { create } from "zustand";
import type { GraphNode, GraphEdge } from "@/types";

interface GraphStore {
  // Graph data (loaded once on mount)
  nodes: GraphNode[];
  edges: GraphEdge[];
  setGraphData: (nodes: GraphNode[], edges: GraphEdge[]) => void;

  // Selected node (by id)
  selectedNodeId: string | null;
  setSelectedNode: (id: string | null) => void;
}

export const useGraphStore = create<GraphStore>((set) => ({
  nodes: [],
  edges: [],
  setGraphData: (nodes, edges) => set({ nodes, edges }),

  selectedNodeId: null,
  setSelectedNode: (id) => set({ selectedNodeId: id }),
}));

// Derived selector — returns the full GraphNode object for the selected id
export function useSelectedNode(): GraphNode | null {
  return useGraphStore((s) =>
    s.selectedNodeId ? (s.nodes.find((n) => n.id === s.selectedNodeId) ?? null) : null
  );
}
