import { Link, Route, Routes } from "react-router-dom";

import AdminDashboardPage from "./pages/AdminDashboardPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import ContestantFormPage from "./pages/ContestantFormPage";
import ExamPage from "./pages/ExamPage";
import HomePage from "./pages/HomePage";
import ResultPage from "./pages/ResultPage";
import RulesPage from "./pages/RulesPage";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur-sm">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <Link to="/" className="text-xl font-bold tracking-tight text-slate-900">
            Exam Portal
          </Link>
          <nav className="flex items-center gap-3 text-sm font-medium">
            <Link to="/" className="rounded-lg px-3 py-2 text-slate-600 transition hover:bg-slate-100">
              Home
            </Link>
            <Link
              to="/admin/login"
              className="rounded-lg px-3 py-2 text-slate-600 transition hover:bg-slate-100"
            >
              Admin
            </Link>
            <Link
              to="/contestant/form"
              className="rounded-lg px-3 py-2 text-slate-600 transition hover:bg-slate-100"
            >
              Contestant
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
          <Route path="/contestant/form" element={<ContestantFormPage />} />
          <Route path="/contestant/rules" element={<RulesPage />} />
          <Route path="/contestant/exam" element={<ExamPage />} />
          <Route path="/contestant/result" element={<ResultPage />} />
        </Routes>
      </main>
    </div>
  );
}
