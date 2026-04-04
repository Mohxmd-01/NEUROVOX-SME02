import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import DashboardPage    from "./pages/DashboardPage";
import RFPProcessorPage from "./pages/RFPProcessorPage";
import KnowledgeBasePage from "./pages/KnowledgeBasePage";
import QuoteHistoryPage from "./pages/QuoteHistoryPage";
import SettingsPage     from "./pages/SettingsPage";
import SourcingPage     from "./pages/SourcingPage";

function Layout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <TopBar />
        <div className="page-body">
          <Routes>
            <Route path="/"          element={<DashboardPage />} />
            <Route path="/rfp"       element={<RFPProcessorPage />} />
            <Route path="/knowledge" element={<KnowledgeBasePage />} />
            <Route path="/quotes"    element={<QuoteHistoryPage />} />
            <Route path="/settings"  element={<SettingsPage />} />
            <Route path="/sourcing"  element={<SourcingPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
