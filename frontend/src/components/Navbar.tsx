export function Navbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-20 h-12 flex items-center justify-between px-4 bg-black/40 backdrop-blur-sm border-b border-white/10">
      <span className="text-sm font-semibold text-white tracking-wide">
        Epstein Files — Network Analysis
      </span>
      <a
        href="/docs/"
        className="text-xs text-white/60 hover:text-white transition-colors"
        target="_blank"
        rel="noopener noreferrer"
      >
        Data Story ↗
      </a>
    </header>
  );
}
