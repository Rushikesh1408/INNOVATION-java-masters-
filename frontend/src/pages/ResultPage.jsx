import { Link } from "react-router-dom";

function getStoredResult() {
  const raw = localStorage.getItem("contestant_result");
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export default function ResultPage() {
  const result = getStoredResult();

  return (
    <section className="mx-auto w-full max-w-2xl rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
      <h1 className="text-2xl font-bold text-slate-900">Result Page</h1>

      {result ? (
        <div className="mt-6 space-y-3">
          <p className="text-slate-700">
            Score: <span className="font-semibold">{result.score}</span> / {result.total}
          </p>
          <p className="text-slate-600">Submitted at: {new Date(result.submittedAt).toLocaleString()}</p>
        </div>
      ) : (
        <p className="mt-6 rounded-lg bg-amber-50 px-4 py-3 text-amber-800">No result found yet.</p>
      )}

      <Link
        to="/"
        className="mt-6 inline-flex rounded-lg bg-slate-900 px-5 py-2.5 font-semibold text-white transition hover:bg-slate-700"
      >
        Back to Home
      </Link>
    </section>
  );
}
