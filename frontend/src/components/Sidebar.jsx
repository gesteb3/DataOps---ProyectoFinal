const menuItems = [
  { label: "Resumen", href: "#overview", icon: "◈" },
  { label: "Rendimiento", href: "#performance", icon: "▣" },
  { label: "Alertas", href: "#alerts", icon: "!" },
  { label: "Backups", href: "#backups", icon: "◆" },
  { label: "Replicación", href: "#replication", icon: "↔" },
  { label: "Auditoría", href: "#audit", icon: "✓" }
];

function Sidebar({ onOpenDemoPanel }) {
  const handleOpenDemoPanel = (event) => {
    event.preventDefault();
    onOpenDemoPanel();
  };

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">D</div>
        <div>
          <strong>DataOps</strong>
          <span>Control Center</span>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Navegación principal">
        {menuItems.map((item) => (
          <a key={item.href} href={item.href}>
            <span>{item.icon}</span>
            {item.label}
          </a>
        ))}

        <button className="sidebar-demo-button" type="button" onClick={handleOpenDemoPanel}>
          <span>⚙</span>
          Demo/Pruebas
        </button>
      </nav>

      <div className="sidebar-card">
        <span>API conectada</span>
        <strong>Centro de Monitoreo</strong>
        <small></small>
      </div>
    </aside>
  );
}

export default Sidebar;
