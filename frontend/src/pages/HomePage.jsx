import { Link } from "react-router-dom";

const roleCards = [
  {
    title: "Admin",
    description: "Manage exams, questions, and leaderboard from a secure control panel.",
    to: "/admin/login",
    action: "Go to Admin Login",
  },
  {
    title: "Contestant",
    description: "Register details, accept exam rules, and begin your timed assessment.",
    to: "/contestant/form",
    action: "Start as Contestant",
  },
];

export default function HomePage() {
  return (
    <section className="space-y-8">
      <div className="rounded-3xl bg-gradient-to-r from-blue-600 to-cyan-500 p-8 text-white shadow-xl sm:p-12">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-100">Online Examination</p>
        <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Secure Exam System</h1>
        <p className="mt-4 max-w-2xl text-blue-50">
          Choose your role to continue. The platform includes anti-cheat checks, timed workflow, and
          role-based access.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {roleCards.map((item) => (
          <article key={item.title} className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="text-2xl font-semibold text-slate-900">{item.title}</h2>
            <p className="mt-3 text-slate-600">{item.description}</p>
            <Link
              to={item.to}
              className="mt-6 inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
            >
              {item.action}
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
