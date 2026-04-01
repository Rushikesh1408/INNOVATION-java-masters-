import { useEffect, useState } from "react";

import { apiRequest } from "../api/client";

export default function AdminDashboardPage() {
  const [token, setToken] = useState("");
  const [exams, setExams] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest("/exams")
      .then(setExams)
      .catch(() => setExams([]));
  }, []);

  const login = async (event) => {
    event.preventDefault();
    setError("");

    const formData = new FormData(event.currentTarget);
    try {
      const response = await apiRequest("/auth/admin/login", {
        method: "POST",
        body: JSON.stringify({
          username: formData.get("username"),
          password: formData.get("password"),
        }),
      });
      setToken(response.access_token);
    } catch {
      setError("Login failed");
    }
  };

  return (
    <section className="stack">
      <h2>Admin Dashboard</h2>

      <form className="card" onSubmit={login}>
        <h3>Admin Login</h3>
        <input name="username" placeholder="Username" required />
        <input name="password" placeholder="Password" type="password" required />
        <button className="button" type="submit">
          Sign In
        </button>
        {error && <p className="error">{error}</p>}
        {token && <p className="success">JWT issued.</p>}
      </form>

      <article className="card">
        <h3>Exam List</h3>
        <ul>
          {exams.map((exam) => (
            <li key={exam.id}>
              {exam.title} ({exam.time_limit} min)
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
}
