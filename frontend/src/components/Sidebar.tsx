import { useSelectedNode, useGraphStore } from "@/store";
import { communityColor } from "@/lib/colors";
import { Button } from "@/components/ui/button";

export function Sidebar() {
  const node = useSelectedNode();
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode);

  if (!node) return null;

  const pct = (node.betweenness_centrality * 100).toFixed(3);
  const color = communityColor(node.community);

  return (
    <aside className="fixed top-12 right-0 bottom-0 z-20 w-80 bg-black/60 backdrop-blur-md border-l border-white/10 overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-white/10">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className="inline-block w-3 h-3 rounded-full shrink-0"
              style={{ backgroundColor: color }}
            />
            <span className="text-xs text-white/50 uppercase tracking-widest">
              {node.type}
            </span>
          </div>
          <h2 className="text-white font-semibold text-base leading-tight capitalize break-words">
            {node.label}
          </h2>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setSelectedNode(null)}
          className="shrink-0 text-white/50 hover:text-white ml-2"
          aria-label="Close"
        >
          ✕
        </Button>
      </div>

      {/* Metrics */}
      <div className="p-4 grid grid-cols-2 gap-3 border-b border-white/10">
        <Metric label="Betweenness" value={`${pct}%`} />
        <Metric label="Degree" value={String(node.degree)} />
        <Metric label="Occurrences" value={String(node.occurrences)} />
        <Metric label="Community" value={String(node.community)} />
      </div>

      {/* Source documents */}
      <div className="p-4">
        <p className="text-xs text-white/40 uppercase tracking-widest mb-3">
          Source documents ({node.source_docs.length})
        </p>
        {node.source_docs.length === 0 ? (
          <p className="text-sm text-white/40 italic">No source documents linked.</p>
        ) : (
          <ul className="space-y-2">
            {node.source_docs.map((doc) => (
              <li key={doc.doc_id}>
                <a
                  href={doc.online_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-400 hover:text-blue-300 hover:underline break-all leading-relaxed block"
                  title={doc.online_url}
                >
                  {doc.file_name || doc.doc_id}
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white/5 rounded-md px-3 py-2">
      <p className="text-xs text-white/40 mb-0.5">{label}</p>
      <p className="text-sm text-white font-medium tabular-nums">{value}</p>
    </div>
  );
}
