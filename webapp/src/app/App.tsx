import { Routes, Route } from "react-router-dom";
import { Shell } from "../components/Shell";
import { useBootstrap } from "../hooks/useBootstrap";
import { DashboardPage } from "../pages/DashboardPage";
import { HistoryPage } from "../pages/HistoryPage";
import { ReportDetailPage } from "../pages/ReportDetailPage";
import { PricingPage } from "../pages/PricingPage";
import { ReferralsPage } from "../pages/ReferralsPage";
import { AdminPage } from "../pages/AdminPage";

export function App() {
  useBootstrap();

  return (
    <Shell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/reports/:id" element={<ReportDetailPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/referrals" element={<ReferralsPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </Shell>
  );
}
