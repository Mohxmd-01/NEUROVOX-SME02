import { useLocation } from "react-router-dom";
import { Bell, Search, HelpCircle } from "lucide-react";

const TITLES = {
  "/":          { title:"Dashboard",       sub:"Welcome back — here's your overview" },
  "/rfp":       { title:"RFP Processor",   sub:"Paste or upload an RFP to get an AI-driven pricing decision" },
  "/sourcing":  { title:"Global Sourcing", sub:"Compare Local · Offshore · Near-Client supply chains" },
  "/knowledge": { title:"Knowledge Base",  sub:"Query company documents and pricing policies" },
  "/quotes":    { title:"Quote History",   sub:"Track, review, and record outcomes for all quotations" },
  "/settings":  { title:"Settings",        sub:"Configure system preferences and data" },
};

export default function TopBar() {
  const { pathname } = useLocation();
  const info = TITLES[pathname] || TITLES["/"];

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div>
          <div style={{ fontSize:".72rem", color:"var(--t3)", fontWeight:500 }}>
            IntelliQuote &rsaquo; {info.title}
          </div>
          <div style={{ fontSize:".92rem", fontWeight:700, color:"var(--t1)", letterSpacing:"-.01em" }}>
            {info.title}
          </div>
        </div>
      </div>
      <div className="topbar-right">
        <button className="topbar-btn" title="Search">
          <Search size={15} />
        </button>
        <button className="topbar-btn" title="Help">
          <HelpCircle size={15} />
        </button>
        <button className="topbar-btn" title="Notifications">
          <Bell size={15} />
        </button>
      </div>
    </header>
  );
}
