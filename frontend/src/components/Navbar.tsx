export function Navbar() {
  return (
    <div
      style={{
        position: "fixed",
        top: 20,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 30,
        background: "#09090b",
        border: "1px solid #27272a",
        borderRadius: 9999,
        padding: "5px 14px",
        boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
        fontFamily: "Inter, sans-serif",
      }}
    >
      <span style={{ fontSize: 13, fontWeight: 500, color: "white" }}>
        Overview
      </span>
    </div>
  );
}
