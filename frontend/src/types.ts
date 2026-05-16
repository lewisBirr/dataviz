export interface SourceDoc {
  doc_id: string;
  file_name: string;
  online_url: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "PERSON" | "ORG" | string;
  betweenness_centrality: number;
  degree: number;
  occurrences: number;
  community: number;
  source_docs: SourceDoc[];
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
