import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

const demoQuestions = [
  {
    id: 1,
    prompt: "What does JVM stand for?",
    options: ["Java Virtual Machine", "Java Vendor Module", "Joint Value Memory", "Just Visual Manager"],
    answer: "Java Virtual Machine",
  },
  {
    id: 2,
    prompt: "Which keyword is used to inherit a class in Java?",
    options: ["this", "super", "extends", "implements"],
    answer: "extends",
  },
];

export default function ExamPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState({});

  const score = useMemo(() => {
    return demoQuestions.reduce((total, question) => {
      return selected[question.id] === question.answer ? total + 1 : total;
    }, 0);
  }, [selected]);

  const submitExam = () => {
    localStorage.setItem(
      "contestant_result",
      JSON.stringify({
        total: demoQuestions.length,
        score,
        submittedAt: new Date().toISOString(),
      })
    );

    navigate("/contestant/result");
  };

  return (
    <section className="space-y-6">
      <header className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-bold text-slate-900">Exam Page</h1>
        <p className="mt-1 text-sm text-slate-500">Answer all questions and submit your exam.</p>
      </header>

      <div className="space-y-4">
        {demoQuestions.map((question, index) => (
          <article key={question.id} className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="font-semibold text-slate-900">
              Q{index + 1}. {question.prompt}
            </h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {question.options.map((option) => {
                const isSelected = selected[question.id] === option;
                return (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setSelected((current) => ({ ...current, [question.id]: option }))}
                    className={`rounded-lg border px-4 py-2 text-left text-sm transition ${
                      isSelected
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-slate-300 bg-white text-slate-700 hover:border-blue-300"
                    }`}
                  >
                    {option}
                  </button>
                );
              })}
            </div>
          </article>
        ))}
      </div>

      <button
        type="button"
        onClick={submitExam}
        className="inline-flex rounded-lg bg-emerald-600 px-5 py-2.5 font-semibold text-white transition hover:bg-emerald-700"
      >
        Submit Exam
      </button>
    </section>
  );
}
