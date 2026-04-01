import { Link, Route, Routes } from "react-router-dom";

import AdminDashboardPage from "./pages/AdminDashboardPage";
import ContestantExamPage from "./pages/ContestantExamPage";
import RoleSelectionPage from "./pages/RoleSelectionPage";

export default function App() {
  return (
    <div className="app-shell">
      <header className="header">
        <h1>Java Masters Exam Engine</h1>
        <nav>
          <Link to="/">Role Selection</Link>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<RoleSelectionPage />} />
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/contestant" element={<ContestantExamPage />} />
        </Routes>
      </main>
    </div>
  );
}
