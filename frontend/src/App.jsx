import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Editor from "@monaco-editor/react";

import { apiClient } from "./api/client";

const DEFAULT_CODE = `public class Main {
    public static void main(String[] args) {
        // Write your solution here
    }
}`;

const initialLoginForm = {
  name: "",
  email: "",
  examId: "1",
};

const STAGES = ["login", "quiz", "result", "coding", "final"];

function formatTime(seconds) {
  const safeSeconds = Math.max(0, Number(seconds) || 0);
  const minutes = Math.floor(safeSeconds / 60)
    .toString()
    .padStart(2, "0");
  const remaining = (safeSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remaining}`;
}

function persistState(state) {
  sessionStorage.setItem("exam-spa-state", JSON.stringify(state));
}

function restoreState() {
  try {
    const raw = sessionStorage.getItem("exam-spa-state");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function App() {
  const [stage, setStage] = useState("login");
  const [loginForm, setLoginForm] = useState(initialLoginForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sessionData, setSessionData] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [questionOpenedAt, setQuestionOpenedAt] = useState({});
  const [quizSecondsLeft, setQuizSecondsLeft] = useState(0);
  const [quizResult, setQuizResult] = useState(null);
  const [codingProblems, setCodingProblems] = useState([]);
  const [selectedProblemId, setSelectedProblemId] = useState(null);
  const [codingCodeMap, setCodingCodeMap] = useState({});
  const [codingResult, setCodingResult] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [antiCheatWarnings, setAntiCheatWarnings] = useState(0);
  const quizTimerRef = useRef(null);
  const submissionInProgressRef = useRef(false);

  useEffect(() => {
    const saved = restoreState();
    if (!saved) {
      return;
    }

    setStage(STAGES.includes(saved.stage) ? saved.stage : "login");
    setLoginForm(saved.loginForm || initialLoginForm);
    setSessionData(saved.sessionData || null);
    setQuestions(saved.questions || []);
    setCurrentQuestionIndex(saved.currentQuestionIndex || 0);
    setAnswers(saved.answers || {});
    setQuestionOpenedAt(saved.questionOpenedAt || {});
    setQuizSecondsLeft(saved.quizSecondsLeft || 0);
    setQuizResult(saved.quizResult || null);
    setCodingProblems(saved.codingProblems || []);
    setSelectedProblemId(saved.selectedProblemId || null);
    setCodingCodeMap(saved.codingCodeMap || {});
    setCodingResult(saved.codingResult || null);
    setLeaderboard(saved.leaderboard || []);
    setAntiCheatWarnings(saved.antiCheatWarnings || 0);
  }, []);

  useEffect(() => {
    persistState({
      stage,
      loginForm,
      sessionData,
      questions,
      currentQuestionIndex,
      answers,
      questionOpenedAt,
      quizSecondsLeft,
      quizResult,
      codingProblems,
      selectedProblemId,
      codingCodeMap,
      codingResult,
      leaderboard,
      antiCheatWarnings,
    });
  }, [
    stage,
    loginForm,
    sessionData,
    questions,
    currentQuestionIndex,
    answers,
    questionOpenedAt,
    quizSecondsLeft,
    quizResult,
    codingProblems,
    selectedProblemId,
    codingCodeMap,
    codingResult,
    leaderboard,
    antiCheatWarnings,
  ]);

  const currentQuestion = questions[currentQuestionIndex] || null;
  const selectedProblem = useMemo(
    () => codingProblems.find((problem) => problem.id === selectedProblemId) || codingProblems[0] || null,
    [codingProblems, selectedProblemId]
  );
  const currentCodingCode = useMemo(() => {
    if (!selectedProblem) {
      return DEFAULT_CODE;
    }
    return codingCodeMap[selectedProblem.id] || selectedProblem.starter_code || DEFAULT_CODE;
  }, [codingCodeMap, selectedProblem]);

  useEffect(() => {
    if (stage !== "quiz") {
      return undefined;
    }

    quizTimerRef.current = window.setInterval(() => {
      setQuizSecondsLeft((current) => {
        if (current <= 1) {
          window.clearInterval(quizTimerRef.current);
          return 0;
        }
        return current - 1;
      });
    }, 1000);

    return () => window.clearInterval(quizTimerRef.current);
  }, [stage]);

  useEffect(() => {
    if (stage !== "quiz" && stage !== "coding") {
      return undefined;
    }

    const preventDefault = (event) => event.preventDefault();
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setAntiCheatWarnings((current) => current + 1);
      }
    };

    document.addEventListener("contextmenu", preventDefault);
    document.addEventListener("copy", preventDefault);
    document.addEventListener("paste", preventDefault);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("contextmenu", preventDefault);
      document.removeEventListener("copy", preventDefault);
      document.removeEventListener("paste", preventDefault);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [stage]);

  useEffect(() => {
    if (!currentQuestion || stage !== "quiz") {
      return;
    }

    setQuestionOpenedAt((current) => {
      if (current[currentQuestion.id]) {
        return current;
      }
      return { ...current, [currentQuestion.id]: Date.now() };
    });
  }, [currentQuestion, stage]);

  useEffect(() => {
    if (stage === "final" && sessionData?.exam?.id) {
      apiClient
        .get(`/coding/leaderboard/${sessionData.exam.id}`)
        .then((response) => setLeaderboard(response.data.leaderboard || []))
        .catch(() => setLeaderboard([]));
    }
  }, [sessionData?.exam?.id, stage]);

  const resetExamState = () => {
    setQuestions([]);
    setCurrentQuestionIndex(0);
    setAnswers({});
    setQuestionOpenedAt({});
    setQuizSecondsLeft(0);
    setQuizResult(null);
    setCodingProblems([]);
    setSelectedProblemId(null);
    setCodingCodeMap({});
    setCodingResult(null);
    setLeaderboard([]);
    setAntiCheatWarnings(0);
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await apiClient.post("/auth/login", {
        name: loginForm.name,
        email: loginForm.email,
        exam_id: loginForm.examId,
      });

      const payload = response.data;
      const exam = payload.exam || {};
      const nextQuestions = (payload.questions || []).map((question) => ({
        ...question,
        options: (question.options || []).map((option) => ({
          id: option.option_id ?? option.id ?? option,
          text: option.text ?? option,
        })),
      }));
      const timerSeconds = Math.max(0, Number(exam.time_limit || 0) * 60);

      setSessionData(payload);
      setQuestions(nextQuestions);
      setQuizSecondsLeft(timerSeconds);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setQuestionOpenedAt({ [nextQuestions[0]?.id || 0]: Date.now() });
      setStage("quiz");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const selectAnswer = (questionId, option) => {
    setAnswers((current) => ({ ...current, [questionId]: option }));
  };

  const goToQuestion = (index) => {
    if (index < 0 || index >= questions.length) {
      return;
    }

    setCurrentQuestionIndex(index);
    setQuestionOpenedAt((current) => ({
      ...current,
      [questions[index].id]: current[questions[index].id] || Date.now(),
    }));
  };

  const handleQuizSubmit = useCallback(async () => {
    if (submissionInProgressRef.current) {
      return;
    }
    if (!sessionData?.session_id || !questions.length) {
      return;
    }

    submissionInProgressRef.current = true;
    try {
      setLoading(true);
      const answersPayload = questions.map((question) => ({
        question_id: question.id,
        selected_option: answers[question.id] ?? null,
        time_taken: Math.max(0, Date.now() - (questionOpenedAt[question.id] || Date.now())),
      }));

      const response = await apiClient.post("/quiz/submit", {
        session_id: sessionData.session_id,
        answers: answersPayload,
      });

      setQuizResult(response.data);
      if (response.data.qualified_for_coding) {
        setStage("result");
      } else {
        setStage("final");
      }
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to submit quiz.");
    } finally {
      submissionInProgressRef.current = false;
      setLoading(false);
    }
  }, [answers, questionOpenedAt, questions, sessionData?.session_id]);

  useEffect(() => {
    if (stage === "quiz" && antiCheatWarnings >= 2) {
      handleQuizSubmit();
    }
  }, [antiCheatWarnings, stage, handleQuizSubmit]);

  useEffect(() => {
    if (stage === "quiz" && quizSecondsLeft === 0 && questions.length) {
      handleQuizSubmit();
    }
  }, [quizSecondsLeft, stage, questions.length, handleQuizSubmit]);

  const loadCodingProblems = async () => {
    if (!sessionData?.exam?.id) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await apiClient.get(`/coding/problems/${sessionData.exam.id}`);
      const problems = response.data.problems || [];
      setCodingProblems(problems);
      setSelectedProblemId(problems[0]?.id || null);
      setCodingCodeMap((current) => {
        const next = { ...current };
        for (const problem of problems) {
          if (!next[problem.id]) {
            next[problem.id] = problem.starter_code || DEFAULT_CODE;
          }
        }
        return next;
      });
      setStage("coding");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to load coding problems.");
    } finally {
      setLoading(false);
    }
  };

  const handleCodingSubmit = async () => {
    if (!selectedProblem) {
      setError("Select a coding problem first.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await apiClient.post(`/coding/submit/${selectedProblem.id}`, {
        code: currentCodingCode,
      });
      setCodingResult(response.data);
      setStage("final");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Coding submission failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Ignore logout failures; clear local state regardless.
    }

    sessionStorage.removeItem("exam-spa-state");
    setStage("login");
    setLoginForm(initialLoginForm);
    setSessionData(null);
    resetExamState();
  };

  const renderStage = () => {
    if (stage === "login") {
      return (
        <section className="grid min-h-[70vh] gap-8 rounded-[2rem] border border-white/10 bg-slate-950/90 p-6 text-white shadow-2xl shadow-slate-950/30 backdrop-blur sm:p-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <div className="inline-flex rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-200">
              Single Website Exam Flow
            </div>
            <div className="space-y-4">
              <h1 className="max-w-xl text-4xl font-black tracking-tight text-white sm:text-5xl">
                Login, quiz, code, and finish without leaving this page.
              </h1>
              <p className="max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
                The SPA keeps the entire exam journey in one state machine: login, Round 1 quiz,
                qualification check, Java coding round, and the final dashboard.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                ["JWT", "HttpOnly cookie session"],
                ["Quiz", "Timer + auto submit"],
                ["Coding", "Docker sandbox execution"],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">{label}</p>
                  <p className="mt-2 text-sm font-medium text-white">{value}</p>
                </div>
              ))}
            </div>
          </div>

          <form
            onSubmit={handleLogin}
            className="rounded-[1.75rem] border border-white/10 bg-white p-6 text-slate-900 shadow-xl sm:p-8"
          >
            <h2 className="text-2xl font-bold tracking-tight">Start Exam Session</h2>
            <p className="mt-2 text-sm text-slate-500">Contestant login creates the session and loads the quiz.</p>

            <div className="mt-6 space-y-4">
              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-700">Full Name</span>
                <input
                  value={loginForm.name}
                  onChange={(event) => setLoginForm((current) => ({ ...current, name: event.target.value }))}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                  required
                />
              </label>

              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-700">Email</span>
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={(event) => setLoginForm((current) => ({ ...current, email: event.target.value }))}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                  required
                />
              </label>

              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-700">Exam ID</span>
                <input
                  value={loginForm.examId}
                  onChange={(event) => setLoginForm((current) => ({ ...current, examId: event.target.value }))}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200"
                  required
                />
              </label>

              {error ? (
                <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
              ) : null}

              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full items-center justify-center rounded-xl bg-slate-950 px-4 py-3 font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {loading ? "Loading session..." : "Enter Exam"}
              </button>
            </div>
          </form>
        </section>
      );
    }

    if (stage === "quiz") {
      return (
        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.4fr]">
          <article className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-5">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-700">Round 1</p>
                <h2 className="mt-1 text-3xl font-bold text-slate-950">Timed Quiz</h2>
                <p className="mt-2 text-sm text-slate-500">Copy, paste, and tab switching are restricted during the test.</p>
              </div>
              <div className="rounded-2xl bg-rose-50 px-4 py-3 text-right ring-1 ring-rose-100">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-700">Time Left</p>
                <p className="mt-1 text-2xl font-black text-rose-800">{formatTime(quizSecondsLeft)}</p>
              </div>
            </div>

            {currentQuestion ? (
              <div className="mt-6 space-y-6">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-slate-500">Question {currentQuestionIndex + 1} of {questions.length}</p>
                    <h3 className="mt-1 text-xl font-semibold text-slate-950">{currentQuestion.question_text}</h3>
                  </div>
                  <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
                    Answered: {Object.keys(answers).length}
                  </div>
                </div>

                <div className="grid gap-3">
                  {(currentQuestion.options || []).map((option, index) => {
                    const optionId = option.id ?? index + 1;
                    const optionText = option.text ?? option;
                    const isSelected = answers[currentQuestion.id] === optionId;
                    return (
                      <button
                        key={`${currentQuestion.id}-${optionId}`}
                        type="button"
                        onClick={() => selectAnswer(currentQuestion.id, optionId)}
                        className={`rounded-2xl border px-4 py-4 text-left transition ${
                          isSelected
                            ? "border-cyan-500 bg-cyan-50 text-cyan-900"
                            : "border-slate-200 bg-slate-50 text-slate-800 hover:border-cyan-300"
                        }`}
                      >
                        <span className="mr-3 inline-flex h-7 w-7 items-center justify-center rounded-full bg-white text-xs font-bold text-slate-700 ring-1 ring-slate-200">
                          {String.fromCharCode(65 + index)}
                        </span>
                        {optionText}
                      </button>
                    );
                  })}
                </div>

                <div className="flex flex-wrap gap-3 border-t border-slate-200 pt-5">
                  <button
                    type="button"
                    onClick={() => goToQuestion(currentQuestionIndex - 1)}
                    disabled={currentQuestionIndex === 0}
                    className="rounded-xl border border-slate-300 px-4 py-2.5 font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    onClick={() => goToQuestion(currentQuestionIndex + 1)}
                    disabled={currentQuestionIndex >= questions.length - 1}
                    className="rounded-xl border border-slate-300 px-4 py-2.5 font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Next
                  </button>
                  <button
                    type="button"
                    onClick={handleQuizSubmit}
                    className="ml-auto rounded-xl bg-slate-950 px-5 py-2.5 font-semibold text-white transition hover:bg-slate-800"
                  >
                    Submit Quiz
                  </button>
                </div>
              </div>
            ) : null}
          </article>

          <aside className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <h3 className="text-lg font-bold text-slate-950">Question Map</h3>
            <div className="mt-4 grid grid-cols-5 gap-2">
              {questions.map((question, index) => {
                const isCurrent = index === currentQuestionIndex;
                const isAnswered = typeof answers[question.id] !== "undefined";
                return (
                  <button
                    key={question.id}
                    type="button"
                    onClick={() => goToQuestion(index)}
                    className={`rounded-xl px-0 py-3 text-sm font-semibold transition ${
                      isCurrent
                        ? "bg-cyan-600 text-white"
                        : isAnswered
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {index + 1}
                  </button>
                );
              })}
            </div>

            <div className="mt-6 space-y-3 rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
              <p className="font-semibold text-slate-900">Anti-cheat</p>
              <p>• Right click, copy, and paste are blocked during the quiz.</p>
              <p>• Leaving the tab increments warnings.</p>
              <p>• Two warnings can auto-submit the quiz.</p>
            </div>
          </aside>
        </section>
      );
    }

    if (stage === "result") {
      return (
        <section className="mx-auto max-w-4xl rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-700">Round 1 Result</p>
              <h2 className="mt-1 text-3xl font-bold text-slate-950">Qualification Check</h2>
            </div>
            <div className={`rounded-2xl px-4 py-3 text-sm font-semibold ${quizResult?.qualified_for_coding ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-800"}`}>
              {quizResult?.qualified_for_coding ? "Qualified for Coding Round" : "Not Qualified"}
            </div>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Score</p>
              <p className="mt-2 text-2xl font-bold text-slate-950">{quizResult?.score ?? 0}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Rank</p>
              <p className="mt-2 text-2xl font-bold text-slate-950">{quizResult?.rank ?? "-"}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Accuracy</p>
              <p className="mt-2 text-2xl font-bold text-slate-950">{quizResult?.result?.accuracy?.toFixed?.(0) ?? 0}%</p>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={loadCodingProblems}
              className="rounded-xl bg-slate-950 px-5 py-2.5 font-semibold text-white transition hover:bg-slate-800"
            >
              Start Coding Round
            </button>
            <button
              type="button"
              onClick={() => setStage("final")}
              className="rounded-xl border border-slate-300 px-5 py-2.5 font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Skip to Final Dashboard
            </button>
          </div>
        </section>
      );
    }

    if (stage === "coding") {
      return (
        <section className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <aside className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xl font-bold text-slate-950">Coding Problems</h2>
            <div className="mt-4 space-y-3">
              {codingProblems.map((problem) => (
                <button
                  key={problem.id}
                  type="button"
                  onClick={() => setSelectedProblemId(problem.id)}
                  className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                    selectedProblem?.id === problem.id
                      ? "border-cyan-500 bg-cyan-50"
                      : "border-slate-200 bg-slate-50 hover:border-cyan-300"
                  }`}
                >
                  <p className="font-semibold text-slate-950">{problem.title}</p>
                  <p className="mt-1 text-sm text-slate-500">{problem.difficulty} · {problem.time_limit_seconds}s</p>
                </button>
              ))}
            </div>
          </aside>

          <article className="rounded-[1.75rem] border border-slate-200 bg-slate-950 p-5 text-white shadow-sm sm:p-6">
            {selectedProblem ? (
              <>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Round 2</p>
                    <h2 className="mt-1 text-3xl font-bold">{selectedProblem.title}</h2>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">{selectedProblem.description}</p>
                  </div>
                  <div className="rounded-2xl bg-white/5 px-4 py-3 text-sm text-slate-200 ring-1 ring-white/10">
                    <p>Time Limit: {selectedProblem.time_limit_seconds}s</p>
                    <p>Memory Limit: {selectedProblem.memory_limit_mb} MB</p>
                  </div>
                </div>

                <div className="mt-6 grid gap-4 xl:grid-cols-[1fr_320px]">
                  <div className="overflow-hidden rounded-2xl border border-white/10 bg-white">
                    <Editor
                      height="520px"
                      defaultLanguage="java"
                      theme="vs-dark"
                      value={currentCodingCode}
                      onChange={(value) => {
                        if (!selectedProblem) {
                          return;
                        }
                        setCodingCodeMap((current) => ({
                          ...current,
                          [selectedProblem.id]: value || "",
                        }));
                      }}
                      options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        lineNumbers: "on",
                        automaticLayout: true,
                      }}
                    />
                  </div>

                  <div className="space-y-4 rounded-2xl bg-white p-4 text-slate-900">
                    <div>
                      <h3 className="font-semibold text-slate-950">Visible Tests</h3>
                      <div className="mt-3 space-y-3">
                        {(selectedProblem.visible_test_cases || []).map((test, index) => (
                          <div key={index} className="rounded-xl bg-slate-50 p-3 text-sm">
                            <p className="font-semibold text-slate-700">Test {index + 1}</p>
                            <p className="mt-1 text-slate-500">Input: {test.input}</p>
                            <p className="text-slate-500">Expected: {test.expected}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {codingResult ? (
                      <div className="rounded-2xl bg-emerald-50 p-4 text-sm text-emerald-800">
                        <p className="font-semibold">Latest Result</p>
                        <p>Status: {codingResult.status}</p>
                        <p>Score: {codingResult.score}/100</p>
                        <p>Execution: {Math.round(codingResult.execution_time_ms || 0)} ms</p>
                      </div>
                    ) : null}

                    {error ? <div className="rounded-2xl bg-rose-50 p-4 text-sm text-rose-700">{error}</div> : null}

                    <button
                      type="button"
                      onClick={handleCodingSubmit}
                      disabled={loading}
                      className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:bg-slate-300"
                    >
                      {loading ? "Evaluating code..." : "Submit Code"}
                    </button>
                  </div>
                </div>
              </>
            ) : null}
          </article>
        </section>
      );
    }

    return (
      <section className="mx-auto max-w-5xl rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-700">Final Dashboard</p>
            <h2 className="mt-1 text-3xl font-bold text-slate-950">All stages completed</h2>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-xl border border-slate-300 px-4 py-2.5 font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Logout
          </button>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Quiz Score</p>
            <p className="mt-2 text-2xl font-bold text-slate-950">{quizResult?.score ?? 0}</p>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Coding Status</p>
            <p className="mt-2 text-2xl font-bold text-slate-950">{codingResult?.status?.toUpperCase?.() || "N/A"}</p>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Execution Time</p>
            <p className="mt-2 text-2xl font-bold text-slate-950">{Math.round(codingResult?.execution_time_ms || 0)} ms</p>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Rank</p>
            <p className="mt-2 text-2xl font-bold text-slate-950">{quizResult?.rank ?? "-"}</p>
          </div>
        </div>

        {leaderboard.length ? (
          <div className="mt-8 overflow-hidden rounded-2xl border border-slate-200">
            <div className="bg-slate-950 px-4 py-3 text-white">
              <h3 className="font-semibold">Live Leaderboard</h3>
            </div>
            <div className="divide-y divide-slate-200">
              {leaderboard.slice(0, 5).map((entry) => (
                <div key={`${entry.user_id}-${entry.rank}`} className="flex items-center justify-between px-4 py-3 text-sm">
                  <span className="font-semibold text-slate-800">#{entry.rank} {entry.name}</span>
                  <span className="text-slate-500">{entry.total_score} pts</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-xl bg-slate-950 px-5 py-2.5 font-semibold text-white transition hover:bg-slate-800"
          >
            Start Over
          </button>
        </div>
      </section>
    );
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.15),_transparent_30%),linear-gradient(180deg,_#020617_0%,_#0f172a_50%,_#e2e8f0_50%,_#f8fafc_100%)] px-4 py-6 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <header className="rounded-[1.5rem] border border-white/10 bg-slate-950/95 px-5 py-4 text-white shadow-xl shadow-slate-950/30 backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-300">Java Masters Exam Engine</p>
              <h1 className="mt-1 text-2xl font-bold">Single Website Exam Platform</h1>
            </div>
            <div className="flex flex-wrap gap-2">
              {STAGES.map((item) => (
                <span
                  key={item}
                  className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${
                    stage === item ? "bg-cyan-400 text-slate-950" : "bg-white/10 text-slate-200"
                  }`}
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        </header>

        {error && stage !== "login" ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        {renderStage()}
      </div>
    </div>
  );
}