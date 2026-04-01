import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function ContestantFormPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", examId: "1" });
  const [formError, setFormError] = useState("");

  const proceedToRules = (event) => {
    event.preventDefault();

    const normalizedForm = Object.fromEntries(
      Object.entries(form).map(([key, value]) => [key, typeof value === "string" ? value.trim() : value])
    );

    if (!normalizedForm.name || !normalizedForm.email || !normalizedForm.examId) {
      setFormError("Please fill in all fields.");
      return;
    }

    setForm(normalizedForm);
    setFormError("");

    try {
      localStorage.setItem("contestant_form", JSON.stringify(normalizedForm));
      navigate("/contestant/rules");
    } catch (error) {
      console.error("Failed to store contestant form", error);
      setFormError("Unable to save your details in this browser. Please try again.");
    }
  };

  return (
    <section className="mx-auto w-full max-w-2xl rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
      <h1 className="text-2xl font-bold text-slate-900">Contestant Registration</h1>
      <p className="mt-2 text-sm text-slate-500">Provide your details before reading exam rules.</p>

      <form className="mt-6 grid gap-4 sm:grid-cols-2" onSubmit={proceedToRules}>
        <label className="sm:col-span-2">
          <span className="mb-1 block text-sm font-medium text-slate-700">Full Name</span>
          <input
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            required
          />
        </label>

        <label className="sm:col-span-2">
          <span className="mb-1 block text-sm font-medium text-slate-700">Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            required
          />
        </label>

        <label className="sm:col-span-2">
          <span className="mb-1 block text-sm font-medium text-slate-700">Exam ID</span>
          <input
            value={form.examId}
            onChange={(event) => setForm((current) => ({ ...current, examId: event.target.value }))}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            required
          />
        </label>

        <button
          type="submit"
          className="sm:col-span-2 inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white transition hover:bg-blue-700"
        >
          Continue to Rules
        </button>
        {formError ? <p className="sm:col-span-2 text-sm text-rose-700">{formError}</p> : null}
      </form>
    </section>
  );
}
