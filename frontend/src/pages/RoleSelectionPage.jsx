import { Link } from "react-router-dom";

export default function RoleSelectionPage() {
  return (
    <section className="card-grid">
      <article className="card">
        <h2>Admin</h2>
        <p>Create exams, manage questions, and monitor participants.</p>
        <Link className="button" to="/admin">
          Continue as Admin
        </Link>
      </article>

      <article className="card">
        <h2>Contestant</h2>
        <p>Register, read exam rules, and attempt the exam in secure mode.</p>
        <Link className="button" to="/contestant">
          Continue as Contestant
        </Link>
      </article>
    </section>
  );
}
