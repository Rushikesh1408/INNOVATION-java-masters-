import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiClient, getMonitoringWebSocketUrl, withAuth } from "../api/client";

export default function AdminDashboardPage() {
  const [token, setToken] = useState(() => localStorage.getItem("admin_token") || "");
  const [exams, setExams] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [monitoring, setMonitoring] = useState({ active_count: 0, participants: [] });
  const [monitoringError, setMonitoringError] = useState("");
  const [liveMode, setLiveMode] = useState("connecting");

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

  useEffect(() => {
    if (!token) {
      setMonitoring({ active_count: 0, participants: [] });
      setMonitoringError("");
      setLiveMode("offline");
      return;
    }

    let socket;
    let pollingId;
    let isMounted = true;

    const loadSnapshot = async () => {
      try {
        const response = await apiClient.get("/admin/monitoring/active", withAuth(token));
        if (isMounted) {
          setMonitoring(response.data || { active_count: 0, participants: [] });
          setMonitoringError("");
        }
      } catch (requestError) {
        if (isMounted) {
          setMonitoringError(requestError.response?.data?.detail || "Unable to load monitoring snapshot.");
        }
      }
    };

    const startPolling = () => {
      setLiveMode("polling");
      loadSnapshot();
      pollingId = window.setInterval(loadSnapshot, 5000);
    };

    try {
      socket = new WebSocket(getMonitoringWebSocketUrl(token));

      socket.onopen = () => {
        if (!isMounted) {
          return;
        }
        setLiveMode("websocket");
        setMonitoringError("");
      };

      socket.onmessage = (event) => {
        if (!isMounted) {
          return;
        }

        try {
          const snapshot = JSON.parse(event.data);
          setMonitoring(snapshot || { active_count: 0, participants: [] });
          setMonitoringError("");
        } catch (parseError) {
          console.error("Invalid monitoring stream payload", parseError);
        }
      };

      socket.onerror = () => {
        if (!isMounted || pollingId) {
          return;
        }
        startPolling();
      };

      socket.onclose = () => {
        if (!isMounted || pollingId) {
          return;
        }
        startPolling();
      };
    } catch {
      startPolling();
    }

    return () => {
      isMounted = false;
      if (socket && socket.readyState <= 1) {
        socket.close();
      }
      if (pollingId) {
        window.clearInterval(pollingId);
      }
    };
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

      <article className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Live Participant Monitoring</h2>
            <p className="text-sm text-slate-500">
              Active participants: <span className="font-semibold">{monitoring.active_count || 0}</span>
            </p>
          </div>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${
              liveMode === "websocket"
                ? "bg-emerald-100 text-emerald-700"
                : liveMode === "polling"
                  ? "bg-amber-100 text-amber-700"
                  : "bg-slate-100 text-slate-600"
            }`}
          >
            {liveMode === "websocket" ? "Live (WebSocket)" : liveMode === "polling" ? "Polling" : "Offline"}
          </span>
        </div>

        {monitoringError ? (
          <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{monitoringError}</p>
        ) : null}

        {!monitoring.participants?.length ? (
          <p className="mt-4 rounded-lg border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500">
            No active participants right now.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Participant</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Exam</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Current Q</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Time / Question</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Warnings</th>
                  <th className="px-3 py-2 text-left font-semibold text-slate-700">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {monitoring.participants.map((participant) => {
                  const entries = Object.entries(participant.time_per_question_ms || {});
                  return (
                    <tr
                      key={participant.session_id}
                      className={participant.suspicious ? "bg-rose-50/60" : "bg-white"}
                    >
                      <td className="px-3 py-3 align-top">
                        <p className="font-semibold text-slate-900">{participant.user_name}</p>
                        <p className="text-xs text-slate-500">{participant.user_email}</p>
                      </td>
                      <td className="px-3 py-3 align-top text-slate-700">{participant.exam_title}</td>
                      <td className="px-3 py-3 align-top text-slate-700">
                        {participant.current_question ?? "-"} / {participant.total_questions}
                      </td>
                      <td className="px-3 py-3 align-top text-xs text-slate-700">
                        {entries.length ? (
                          <div className="flex flex-wrap gap-2">
                            {entries.map(([questionId, ms]) => (
                              <span key={`${participant.session_id}-${questionId}`} className="rounded bg-slate-100 px-2 py-1">
                                Q{questionId}: {Math.round(ms / 1000)}s
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-500">No responses yet</span>
                        )}
                      </td>
                      <td className="px-3 py-3 align-top text-slate-700">{participant.warning_count}</td>
                      <td className="px-3 py-3 align-top">
                        {participant.suspicious ? (
                          <span className="rounded-full bg-rose-100 px-2 py-1 text-xs font-semibold text-rose-700">
                            Suspicious
                          </span>
                        ) : (
                          <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">
                            Normal
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
