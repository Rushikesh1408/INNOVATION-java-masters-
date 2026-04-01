import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiClient, withAuth } from "../api/client";

export default function AdminDashboardPage() {
  const [token, setToken] = useState(() => localStorage.getItem("admin_token") || "");
  const [exams, setExams] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      setError("Please login as admin to view dashboard data.");
      return;
    }

    setLoading(true);
    apiClient
      .get("/exams", withAuth(token))
      .then((response) => {
        setExams(response.data || []);
        setError("");
      })
      .catch((requestError) => {
        setExams([]);
        setError(requestError.response?.data?.detail || "Unable to load exams.");
      })
      .finally(() => setLoading(false));
  }, [token]);

  const logout = () => {
    localStorage.removeItem("admin_token");
    setToken("");
  };

  if (!token) {
    return (
      <section className="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
        <p className="mt-2 text-slate-600">{error}</p>
        <Link
          to="/admin/login"
          className="mt-6 inline-flex rounded-lg bg-slate-900 px-4 py-2 font-semibold text-white transition hover:bg-slate-700"
        >
          Go to Login
        </Link>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
          <p className="text-sm text-slate-500">Manage available exams and monitor activity.</p>
        </div>
        <button
          type="button"
          onClick={logout}
          className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700"
        >
          Logout
        </button>
      </div>

      <article className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold text-slate-900">Exam List</h2>
        {loading ? <p className="mt-4 text-sm text-slate-500">Loading exams...</p> : null}
        {error ? <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
        {!loading && !error ? (
          <ul className="mt-4 grid gap-3">
            {exams.length ? (
              exams.map((exam) => (
                <li key={exam.id} className="rounded-lg border border-slate-200 px-4 py-3 text-sm text-slate-700">
                  <span className="font-semibold text-slate-900">{exam.title}</span> ({exam.time_limit} min)
                </li>
              ))
            ) : (
              <li className="rounded-lg border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500">
                No exams found.
              </li>
            )}
          </ul>
        ) : null}
      </article>
    </section>
  );
}
