import { useCallback, useEffect, useMemo, useState } from "react";
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
  const [currentIndex, setCurrentIndex] = useState(0);
  const [visited, setVisited] = useState(() =>
    demoQuestions.length > 0 ? new Set([demoQuestions[0].id]) : new Set()
  );
  const [skipped, setSkipped] = useState(() => new Set());
  const [hasStarted, setHasStarted] = useState(false);
  const [timeLeft, setTimeLeft] = useState(60 * 30);

  const safeIndex = demoQuestions.length ? Math.min(Math.max(currentIndex, 0), demoQuestions.length - 1) : 0;
  const currentQuestion = demoQuestions[safeIndex];

  useEffect(() => {
    if (!demoQuestions.length) {
      return;
    }
    if (currentIndex !== safeIndex) {
      setCurrentIndex(safeIndex);
    }
  }, [currentIndex, safeIndex]);

  useEffect(() => {
    if (!hasStarted) {
      return undefined;
    }

    const timerId = window.setInterval(() => {
      setTimeLeft((current) => {
        if (current <= 1) {
          window.clearInterval(timerId);
          return 0;
        }
        return current - 1;
      });
    }, 1000);

    return () => window.clearInterval(timerId);
  }, [hasStarted]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0");
    const secs = (seconds % 60).toString().padStart(2, "0");
    return `${mins}:${secs}`;
  };

  const getStatus = (questionId) => {
    if (selected[questionId]) {
      return "answered";
    }
    if (skipped.has(questionId)) {
      return "skipped";
    }
    if (visited.has(questionId)) {
      return "visited";
    }
    return "not-visited";
  };

  const statusLabel = {
    answered: "Answered",
    skipped: "Skipped",
    visited: "Visited",
    "not-visited": "Not Visited",
  };

  const statusClass = {
    answered: "border-emerald-300 bg-emerald-100 text-emerald-800",
    skipped: "border-amber-300 bg-amber-100 text-amber-800",
    visited: "border-blue-300 bg-blue-100 text-blue-800",
    "not-visited": "border-slate-300 bg-white text-slate-600",
  };

  useEffect(() => {
    if (!demoQuestions.length || !currentQuestion) {
      return;
    }
    setVisited((current) => new Set(current).add(currentQuestion.id));
  }, [demoQuestions.length, currentQuestion]);

  const score = useMemo(() => {
    return demoQuestions.reduce((total, question) => {
      return selected[question.id] === question.answer ? total + 1 : total;
    }, 0);
  }, [selected]);

  const startExam = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      }
    } catch {
      // Continue exam even if fullscreen permission is denied.
    }
    setHasStarted(true);
  };

  const jumpToQuestion = (index) => {
    if (!demoQuestions.length) {
      return;
    }

    const boundedIndex = Math.min(Math.max(index, 0), demoQuestions.length - 1);
    const nextQuestion = demoQuestions[boundedIndex];

    setCurrentIndex(boundedIndex);
    if (nextQuestion?.id !== undefined) {
      setVisited((current) => new Set(current).add(nextQuestion.id));
    }
  };

  const selectOption = (option) => {
    if (!currentQuestion) {
      return;
    }

    const questionId = currentQuestion.id;
    setSelected((current) => ({ ...current, [questionId]: option }));
    setSkipped((current) => {
      const clone = new Set(current);
      clone.delete(questionId);
      return clone;
    });
  };

  const goNext = () => {
    if (currentIndex < demoQuestions.length - 1) {
      jumpToQuestion(currentIndex + 1);
    }
  };

  const markSkipAndNext = () => {
    if (!currentQuestion) {
      return;
    }

    const questionId = currentQuestion.id;
    setSkipped((current) => new Set(current).add(questionId));
    goNext();
  };

  const clearResponse = () => {
    if (!currentQuestion) {
      return;
    }

    const questionId = currentQuestion.id;
    setSelected((current) => {
      const clone = { ...current };
      delete clone[questionId];
      return clone;
    });
  };

  const submitExam = useCallback(() => {
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    }

    const attempted = Object.keys(selected).length;
    localStorage.setItem(
      "contestant_result",
      JSON.stringify({
        total: demoQuestions.length,
        score,
        attempted,
        skipped: skipped.size,
        submittedAt: new Date().toISOString(),
      })
    );

    navigate("/contestant/result");
  }, [navigate, score, selected, skipped]);

  useEffect(() => {
    if (timeLeft === 0 && hasStarted) {
      submitExam();
    }
  }, [timeLeft, hasStarted, submitExam]);

  if (!hasStarted) {
    return (
      <section className="mx-auto max-w-3xl rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-bold text-slate-900">JEE-Style Exam Interface</h1>
        <p className="mt-2 text-slate-600">
          Click start to enter fullscreen mode and begin the timed exam.
        </p>
        <button
          type="button"
          onClick={startExam}
          className="mt-6 inline-flex rounded-lg bg-slate-900 px-5 py-2.5 font-semibold text-white transition hover:bg-slate-700"
        >
          Start Exam in Fullscreen
        </button>
      </section>
    );
  }

  if (!demoQuestions.length || !currentQuestion) {
    return (
      <section className="mx-auto max-w-3xl rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-bold text-slate-900">Exam Unavailable</h1>
        <p className="mt-2 text-slate-600">No questions are available for this exam right now.</p>
      </section>
    );
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <article className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Question {currentIndex + 1}</h1>
            <p className="text-sm text-slate-500">Total Questions: {demoQuestions.length}</p>
          </div>
          <div className="rounded-lg bg-rose-50 px-4 py-2 text-lg font-bold text-rose-700 ring-1 ring-rose-200">
            Time Left: {formatTime(timeLeft)}
          </div>
        </div>

        <p className="mt-5 text-lg font-medium text-slate-900">{currentQuestion.prompt}</p>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {currentQuestion.options.map((option) => {
            const isSelected = selected[currentQuestion.id] === option;
            return (
              <button
                key={option}
                type="button"
                onClick={() => selectOption(option)}
                className={`rounded-lg border px-4 py-3 text-left text-sm transition ${
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

        <div className="mt-8 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={clearResponse}
            className="rounded-lg bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-800 transition hover:bg-slate-300"
          >
            Clear Response
          </button>
          <button
            type="button"
            onClick={markSkipAndNext}
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-600"
          >
            Skip for Now
          </button>
          <button
            type="button"
            onClick={goNext}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            Save and Next
          </button>
          <button
            type="button"
            onClick={submitExam}
            className="ml-auto rounded-lg bg-emerald-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
          >
            Submit Exam
          </button>
        </div>
      </article>

      <aside className="space-y-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold text-slate-900">Question Palette</h2>

        <div className="grid grid-cols-5 gap-2">
          {demoQuestions.map((question, index) => {
            const status = getStatus(question.id);
            const isCurrent = index === currentIndex;
            return (
              <button
                key={question.id}
                type="button"
                onClick={() => jumpToQuestion(index)}
                className={`rounded-lg border px-2 py-2 text-sm font-semibold ${statusClass[status]} ${
                  isCurrent ? "ring-2 ring-slate-900" : ""
                }`}
              >
                {index + 1}
              </button>
            );
          })}
        </div>

        <div className="space-y-2 text-sm">
          {Object.keys(statusLabel).map((key) => (
            <div key={key} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2">
              <span>{statusLabel[key]}</span>
              <span className="font-semibold">
                {demoQuestions.filter((item) => getStatus(item.id) === key).length}
              </span>
            </div>
          ))}
        </div>
      </aside>
    </section>
  );
}
