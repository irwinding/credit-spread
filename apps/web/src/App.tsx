import { Navigate, Route, Routes } from "react-router-dom";

import { DashboardLayout } from "./components/DashboardLayout";
import { Dashboard } from "./pages/Dashboard";
import { Groupings } from "./pages/Groupings";
import { OptionDetail } from "./pages/OptionDetail";
import { SpreadDetail } from "./pages/SpreadDetail";

export function App() {
  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/spreads" replace />} />
        <Route path="/spreads" element={<Dashboard section="spreads" />} />
        <Route path="/options" element={<Dashboard section="options" />} />
        <Route path="/gains" element={<Dashboard section="gains" />} />
        <Route path="/spread/:id" element={<SpreadDetail />} />
        <Route path="/option/:id" element={<OptionDetail />} />
        <Route path="/groupings" element={<Groupings />} />
      </Routes>
    </DashboardLayout>
  );
}
