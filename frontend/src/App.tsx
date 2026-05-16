import { Navbar } from "@/components/Navbar";
import { GraphView } from "@/components/GraphView";
import { Sidebar } from "@/components/Sidebar";

export default function App() {
  return (
    <div className="dark" style={{ background: "#0D1117", width: "100vw", height: "100vh", overflow: "hidden" }}>
      <Navbar />
      {/* Graph fills full viewport; navbar + sidebar overlay it */}
      <div className="absolute inset-0 pt-12">
        <GraphView />
      </div>
      <Sidebar />
    </div>
  );
}
