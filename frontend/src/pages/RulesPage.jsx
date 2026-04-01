import { useNavigate } from "react-router-dom";

const rules = [
  "You must stay on the exam page until submission.",
  "Do not refresh the browser while the exam is active.",
  "Any suspicious activity may auto-submit your exam.",
  "Read each question carefully before answering.",
];

export default function RulesPage() {
  const navigate = useNavigate();

  return (
    <section className="mx-auto w-full max-w-3xl rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
      <h1 className="text-2xl font-bold text-slate-900">Exam Rules</h1>
      <p className="mt-2 text-slate-600">You must accept the rules before starting the exam.</p>

      <ul className="mt-6 space-y-3">
        {rules.map((rule) => (
          <li key={rule} className="rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700 ring-1 ring-slate-200">
            {rule}
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={() => navigate("/contestant/exam")}
        className="mt-6 inline-flex rounded-lg bg-slate-900 px-5 py-2.5 font-semibold text-white transition hover:bg-slate-700"
      >
        I Agree, Start Exam
      </button>
    </section>
  );
}
