import { useState } from "react";

import { apiRequest } from "../api/client";
import { useAntiCheat } from "../hooks/useAntiCheat";

export default function ContestantExamPage() {
  const [sessionId, setSessionId] = useState("");
  const [formError, setFormError] = useState("");
  const [formState, setFormState] = useState({
    name: "",
    email: "",
    examId: "1",
  });

  const { warnings } = useAntiCheat(sessionId);

  const startExam = async (event) => {
    event.preventDefault();
    setFormError("");

    try {
      const user = await apiRequest("/contestants/register", {
        method: "POST",
        body: JSON.stringify({
          name: formState.name,
          email: formState.email,
        }),
      });

      const started = await apiRequest("/contestants/start-exam", {
        method: "POST",
        body: JSON.stringify({
          user_id: user.id,
          exam_id: Number(formState.examId),
        }),
      });

      setSessionId(started.session_id);
    } catch {
      setFormError("Unable to start exam.");
    }
  };

  return (
    <section className="stack">
      <h2>Contestant Exam Interface</h2>
      <p>Warnings: {warnings}</p>

      {!sessionId ? (
        <form className="card" onSubmit={startExam}>
          <h3>Registration</h3>
          <input
            value={formState.name}
            onChange={(event) =>
              setFormState((current) => ({ ...current, name: event.target.value }))
            }
            placeholder="Full name"
            required
          />
          <input
            value={formState.email}
            onChange={(event) =>
              setFormState((current) => ({ ...current, email: event.target.value }))
            }
            placeholder="Email"
            type="email"
            required
          />
          <input
            value={formState.examId}
            onChange={(event) =>
              setFormState((current) => ({ ...current, examId: event.target.value }))
            }
            placeholder="Exam ID"
            required
          />
          <button className="button" type="submit">
            Start Exam
          </button>
          {formError && <p className="error">{formError}</p>}
        </form>
      ) : (
        <article className="card">
          <h3>Exam In Progress</h3>
          <p>Session: {sessionId}</p>
          <p>Timer and question navigator should be rendered here.</p>
        </article>
      )}
    </section>
  );
}
