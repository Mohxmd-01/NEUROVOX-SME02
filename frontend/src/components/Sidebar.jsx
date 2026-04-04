import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, FileText, BookOpen,
  History, Settings, Zap, Globe,
} from "lucide-react";

const NAV = [
  { to:"/",         icon:LayoutDashboard, label:"Dashboard",       color:"#38bdf8" },
  { to:"/rfp",      icon:FileText,        label:"RFP Processor",   color:"#38bdf8", badge:"AI" },
  { to:"/sourcing", icon:Globe,           label:"Global Sourcing", color:"#10b981", badge:"New" },
  { to:"/knowledge",icon:BookOpen,        label:"Knowledge Base",  color:"#f59e0b" },
  { to:"/quotes",   icon:History,         label:"Quote History",   color:"#a78bfa" },
  { to:"/settings", icon:Settings,        label:"Settings",        color:"rgba(255,255,255,0.4)" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sb-brand">
        <div className="sb-logo">
          <Zap size={19} color="white" />
        </div>
        <div>
          <div className="sb-brand-name">IntelliQuote</div>
          <div className="sb-brand-tag">Global Sourcing & Pricing</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="sb-section">
        <div className="sb-section-label">Main Menu</div>
        {NAV.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) => `sb-item ${isActive ? "active" : ""}`}
          >
            <div className="sb-icon" style={{ color: item.color }}>
              <item.icon size={17} />
            </div>
            <span style={{ flex:1 }}>{item.label}</span>
            {item.badge && <span className="sb-badge">{item.badge}</span>}
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="sb-footer">
        <div className="sb-user">
          <div className="sb-avatar">SU</div>
          <div>
            <div className="sb-user-name">Sales User</div>
            <div className="sb-user-role">TechFlow Industries</div>
          </div>
          <div className="sb-status-dot" title="System Online" />
        </div>
      </div>
    </aside>
  );
}
