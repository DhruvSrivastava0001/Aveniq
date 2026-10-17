import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  Download,
  FileText,
  LoaderCircle,
  MessageCircle,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
  RefreshCw,
} from "lucide-react";
import { fetchAPI, postAPI } from "../api";

const panel =
  "rounded-2xl border border-slate-800 bg-slate-900 p-5 md:p-6";
const input =
  "w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 outline-none focus:border-blue-500";
const button =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50";

// Merge partner aliases into the canonical names used by the dashboard.
const normalizePartner = (name) => {
  const value = String(name ?? "").trim();
  const key = value.toLowerCase();

  const aliases = {
    jio: "Reliance Jio",
    "reliance jio": "Reliance Jio",
    vodafone: "Vi",
    vi: "Vi",
  };

  return aliases[key] || value;
};

function Metric({ label, value, detail }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-bold text-white">{value}</p>
      {detail && <p className="mt-1 text-xs text-slate-500">{detail}</p>}
    </div>
  );
}

function ErrorMessage({ children }) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-rose-900/70 bg-rose-950/30 p-3 text-sm text-rose-300">
      <AlertTriangle size={17} className="mt-0.5 shrink-0" />
      <span>{children}</span>
    </div>
  );
}

export default function Intelligence() {
  const [tab, setTab] = useState("assistant");

  const [overview, setOverview] = useState(null);
  const [overviewError, setOverviewError] = useState("");
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewUpdatedAt, setOverviewUpdatedAt] = useState(null);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I can analyze your customer data and explain observed churn metrics. With an OpenAI API key configured on the backend, I can also help with general knowledge, coding, writing, and productivity questions. Try: “Which partner has the highest churn rate?”",
    },
  ]);
  const [chatLoading, setChatLoading] = useState(false);

  const [partner, setPartner] = useState("");
  const [state, setState] = useState("");
  const [investigation, setInvestigation] = useState(null);
  const [investigationError, setInvestigationError] = useState("");
  const [investigationLoading, setInvestigationLoading] = useState(false);

  const [reportLoading, setReportLoading] = useState(false);
  const [reportMessage, setReportMessage] = useState("");

  const [alertSettings, setAlertSettings] = useState({
    churn_rate_threshold: 25,
    minimum_segment_size: 30,
    enabled: true,
  });

  const [alerts, setAlerts] = useState(null);
  const [alertHistory, setAlertHistory] = useState([]);
  const [alertLoading, setAlertLoading] = useState(false);
  const [alertMessage, setAlertMessage] = useState("");
  const [alertError, setAlertError] = useState("");
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyUpdatedAt, setHistoryUpdatedAt] = useState(null);

  const number = (value) =>
    Number(value || 0).toLocaleString("en-IN");

  const loadOverview = useCallback(async () => {
    setOverviewLoading(true);
    setOverviewError("");

    try {
      const data = await fetchAPI("/api/intelligence/overview");
      setOverview(data);
      setOverviewUpdatedAt(new Date());
    } catch (error) {
      setOverviewError(
        error.message || "Unable to refresh intelligence."
      );
    } finally {
      setOverviewLoading(false);
    }
  }, []);

  const loadAlertSettings = useCallback(async () => {
    try {
      const data = await fetchAPI("/api/intelligence/alerts");

      setAlertSettings({
        churn_rate_threshold: data.churn_rate_threshold,
        minimum_segment_size: data.minimum_segment_size,
        enabled: data.enabled,
      });
    } catch (error) {
      setAlertError(
        error.message || "Unable to load alert settings."
      );
    }
  }, []);

  const loadAlertHistory = useCallback(async () => {
    setHistoryLoading(true);
    setAlertError("");

    try {
      const result = await fetchAPI(
        "/api/intelligence/alerts/history?limit=20"
      );

      if (!Array.isArray(result.items)) {
        throw new Error(
          "The history API did not return an items array."
        );
      }

      setAlertHistory(result.items);
      setHistoryUpdatedAt(new Date());
    } catch (error) {
      setAlertError(
        error.message || "Unable to refresh monitoring history."
      );
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOverview();
    loadAlertSettings();
    loadAlertHistory();
  }, [loadOverview, loadAlertSettings, loadAlertHistory]);

  // Normalize names and remove duplicate dropdown options.
  const partners = useMemo(() => {
    const rawPartners = overview?.by_partner || [];

    return [
      ...new Set(
        rawPartners
          .map((row) => normalizePartner(row.telecom_partner))
          .filter(Boolean)
      ),
    ].sort((a, b) => a.localeCompare(b));
  }, [overview]);

  const states = useMemo(() => {
    return [
      ...new Set(
        (overview?.by_state || [])
          .map((row) => row.state)
          .filter(Boolean)
      ),
    ].sort((a, b) => a.localeCompare(b));
  }, [overview]);

  async function ask(questionText = question) {
    const clean = questionText.trim();

    if (!clean || chatLoading) return;

    setQuestion("");
    setMessages((old) => [
      ...old,
      { role: "user", text: clean },
    ]);
    setChatLoading(true);

    try {
      const result = await postAPI("/api/intelligence/chat", {
        question: clean,
      });

      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          text: result.answer,
          sources: result.sources,
          grounded: result.grounded,
          mode: result.mode,
        },
      ]);
    } catch (error) {
      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          text: `I couldn't retrieve the answer. Check that the API and database are running. Details: ${
            error.message || "API request failed"
          }`,
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  async function runInvestigation(event) {
    event.preventDefault();
    setInvestigationLoading(true);
    setInvestigationError("");
    setInvestigation(null);

    try {
      const result = await postAPI(
        "/api/intelligence/investigate",
        {
          // Send the canonical partner name to the backend.
          telecom_partner: partner || null,
          state: state || null,
          focus: "churn",
        }
      );

      setInvestigation(result);
    } catch (error) {
      setInvestigationError(
        error.message ||
          "Investigation failed. Check the API and selected filters."
      );
    } finally {
      setInvestigationLoading(false);
    }
  }

  async function downloadReport() {
    setReportLoading(true);
    setReportMessage("");

    try {
      const base =
        import.meta.env.VITE_PYTHON_API_URL ||
        "http://127.0.0.1:8003";

      const response = await fetch(
        `${base}/api/intelligence/report.csv`
      );

      if (!response.ok) {
        throw new Error(
          `Report endpoint returned ${response.status}`
        );
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = `churniq_customer_report_${new Date()
        .toISOString()
        .slice(0, 10)}.csv`;

      document.body.appendChild(link);
      link.click();
      link.remove();
      // Let the browser begin the download before releasing the blob URL.
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);

      setReportMessage("CSV report downloaded successfully.");
    } catch (error) {
      setReportMessage(
        `Report download failed: ${
          error.message || "API request failed"
        }`
      );
    } finally {
      setReportLoading(false);
    }
  }

  async function saveAlerts(event) {
    event.preventDefault();
    setAlertLoading(true);
    setAlertError("");
    setAlertMessage("");

    try {
      const saved = await fetchAPI("/api/intelligence/alerts", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...alertSettings,
          churn_rate_threshold: Number(
            alertSettings.churn_rate_threshold
          ),
          minimum_segment_size: Number(
            alertSettings.minimum_segment_size
          ),
        }),
      });

      setAlertSettings({
        churn_rate_threshold: saved.churn_rate_threshold,
        minimum_segment_size: saved.minimum_segment_size,
        enabled: saved.enabled,
      });

      setAlertMessage("Alert settings saved successfully.");
    } catch (error) {
      setAlertError(
        error.message || "Unable to save alert settings."
      );
    } finally {
      setAlertLoading(false);
    }
  }

  async function evaluateAlerts() {
    setAlertLoading(true);
    setAlertError("");
    setAlertMessage("");

    try {
      const result = await fetchAPI(
        "/api/intelligence/alerts/evaluate"
      );

      setAlerts(result);
      setAlertMessage("Monitoring evaluation completed.");

      await loadAlertHistory();
    } catch (error) {
      setAlertError(
        error.message || "Unable to evaluate alerts."
      );
    } finally {
      setAlertLoading(false);
    }
  }

  const tabs = [
    ["assistant", MessageCircle, "AI Analyst"],
    ["investigate", Search, "Investigations"],
    ["reports", FileText, "Reports"],
    ["alerts", Activity, "Monitoring & Alerts"],
  ];

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-2xl border border-blue-900/60 bg-gradient-to-br from-blue-950 via-slate-900 to-slate-900 p-6 md:p-8">
        <div className="relative flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div className="max-w-3xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-blue-800 bg-blue-950/70 px-3 py-1 text-xs font-medium text-blue-200">
              <Sparkles size={14} />
              Grounded customer intelligence
            </div>

            <h3 className="text-2xl font-bold text-white md:text-3xl">
              From customer data to clear decisions.
            </h3>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
              Ask questions about your customer data or use the assistant for general
              knowledge, coding, writing, and productivity. Configure OPENAI_API_KEY
              on the backend for general-purpose AI; customer analytics work without it.
            </p>
          </div>

          <button
            type="button"
            onClick={loadOverview}
            disabled={overviewLoading}
            className={`${button} shrink-0`}
          >
            <RefreshCw
              size={16}
              className={overviewLoading ? "animate-spin" : ""}
            />
            {overviewLoading
              ? "Refreshing..."
              : "Refresh intelligence"}
          </button>
        </div>

        {overviewUpdatedAt && (
          <p className="relative mt-3 text-xs text-emerald-300">
            Intelligence refreshed at{" "}
            {overviewUpdatedAt.toLocaleTimeString()}
          </p>
        )}

        {overviewError && (
          <div className="relative mt-4">
            <ErrorMessage>{overviewError}</ErrorMessage>
          </div>
        )}

        {overviewLoading && !overview && (
          <p className="relative mt-4 flex items-center gap-2 text-sm text-slate-300">
            <LoaderCircle size={16} className="animate-spin" />
            Loading customer intelligence...
          </p>
        )}

        {overview?.summary && (
          <div className="relative mt-6 grid gap-3 sm:grid-cols-3">
            <Metric
              label="Customers in current dataset"
              value={number(overview.summary.total_customers)}
            />
            <Metric
              label="Observed churn rate"
              value={`${Number(
                overview.summary.churn_rate || 0
              ).toFixed(2)}%`}
              detail="Descriptive, not a forecast"
            />
            <Metric
              label="Recorded churn cases"
              value={number(overview.summary.churned_customers)}
            />
          </div>
        )}
      </section>

      <div className="flex gap-2 overflow-x-auto border-b border-slate-800 pb-2">
        {tabs.map(([id, Icon, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium transition ${
              tab === id
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:bg-slate-800 hover:text-white"
            }`}
          >
            <Icon size={17} />
            {label}
          </button>
        ))}
      </div>

      {tab === "assistant" && (
        <section className={panel}>
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-blue-500/10 p-3 text-blue-300">
              <Bot size={23} />
            </div>
            <div>
              <h3 className="font-semibold text-white">
                Aveniq AI Assistant
              </h3>
              <p className="mt-1 text-xs text-slate-400">
                Ask about your data or general topics such as Java, SQL, writing, and study.
              </p>
            </div>
          </div>

          <div className="mb-4 flex flex-wrap gap-2">
            {[
              "Which partner has the highest churn rate?",
              "What is the overall churn rate?",
              "How many customers are recorded?",
              "Which state has the lowest churn rate?",
              "Explain REST APIs in simple words",
            ].map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => ask(q)}
                disabled={chatLoading}
                className="rounded-full border border-slate-700 px-3 py-2 text-xs text-slate-300 hover:border-blue-600 hover:text-white disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>

          <div className="mb-4 max-h-[440px] space-y-3 overflow-y-auto rounded-xl border border-slate-800 bg-slate-950 p-4">
            {messages.map((message, index) => (
              <div
                key={`${index}-${message.role}`}
                className={`flex ${
                  message.role === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "border border-slate-800 bg-slate-900 text-slate-200"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.text}</p>
                  {message.mode && (
                    <p className="mt-2 text-[10px] font-medium uppercase tracking-wide text-blue-300">
                      {message.grounded ? "Customer-data answer" : "General AI answer"}
                    </p>
                  )}
                  {message.sources && (
                    <p className="mt-2 border-t border-slate-700 pt-2 text-[11px] text-slate-500">
                      Sources: {message.sources.join(" · ")}
                    </p>
                  )}
                </div>
              </div>
            ))}

            {chatLoading && (
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <LoaderCircle size={16} className="animate-spin" />
                Thinking and checking relevant data...
              </div>
            )}
          </div>

          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              ask();
            }}
          >
            <input
              className={input}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask about customers, Java, SQL, writing, or anything else..."
              maxLength={1000}
            />
            <button
              type="submit"
              className={button}
              disabled={chatLoading || question.trim().length < 2}
            >
              <Send size={16} />
              <span className="hidden sm:inline">Ask</span>
            </button>
          </form>

          <p className="mt-3 text-xs text-amber-300/80">
            The current model's ROC-AUC is approximately 0.50.
            Results describe observed data and should not be treated
            as reliable individual churn predictions.
          </p>
        </section>
      )}

      {tab === "investigate" && (
        <section className={panel}>
          <div className="mb-5 flex items-start gap-3">
            <div className="rounded-xl bg-violet-500/10 p-3 text-violet-300">
              <Target size={22} />
            </div>
            <div>
              <h3 className="font-semibold text-white">
                Controlled segment investigation
              </h3>
              <p className="mt-1 text-sm text-slate-400">
                Select filters and analyse customer segments.
              </p>
            </div>
          </div>

          <form
            onSubmit={runInvestigation}
            className="grid gap-4 md:grid-cols-3"
          >
            <label className="text-sm text-slate-300">
              Telecom partner
              <select
                className={`${input} mt-2`}
                value={partner}
                onChange={(event) => setPartner(event.target.value)}
              >
                <option value="">All partners</option>
                {partners.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm text-slate-300">
              State
              <select
                className={`${input} mt-2`}
                value={state}
                onChange={(event) => setState(event.target.value)}
              >
                <option value="">All states</option>
                {states.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <div className="flex items-end">
              <button
                type="submit"
                className={`${button} w-full`}
                disabled={investigationLoading}
              >
                {investigationLoading ? (
                  <LoaderCircle size={16} className="animate-spin" />
                ) : (
                  <Search size={16} />
                )}
                Investigate segment
              </button>
            </div>
          </form>

          {investigationError && (
            <div className="mt-4">
              <ErrorMessage>{investigationError}</ErrorMessage>
            </div>
          )}

          {investigation && (
            <div className="mt-6 space-y-5">
              <div className="grid gap-3 sm:grid-cols-3">
                <Metric
                  label="Segment customers"
                  value={number(investigation.summary?.total_customers)}
                />
                <Metric
                  label="Observed churn rate"
                  value={`${Number(
                    investigation.summary?.churn_rate || 0
                  ).toFixed(2)}%`}
                />
                <Metric
                  label="Churn-labelled customers"
                  value={number(
                    investigation.summary?.churned_customers
                  )}
                />
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                  <h4 className="font-semibold text-white">Findings</h4>
                  <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-300">
                    {(investigation.findings || []).map(
                      (item, index) => (
                        <li key={index}>{item}</li>
                      )
                    )}
                  </ul>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                  <h4 className="font-semibold text-white">
                    Recommended next steps
                  </h4>
                  <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-300">
                    {(investigation.recommendations || []).map(
                      (item, index) => (
                        <li key={index}>{item}</li>
                      )
                    )}
                  </ul>
                </div>
              </div>

              <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-4">
                <h4 className="flex items-center gap-2 font-semibold text-amber-200">
                  <ShieldCheck size={17} />
                  Limitations and guardrails
                </h4>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-amber-100/80">
                  {(investigation.limitations || []).map(
                    (item, index) => (
                      <li key={index}>{item}</li>
                    )
                  )}
                </ul>
              </div>
            </div>
          )}
        </section>
      )}

      {tab === "reports" && (
        <section className={panel}>
          <div className="mb-5 flex items-center gap-3">
            <div className="rounded-xl bg-emerald-500/10 p-3 text-emerald-300">
              <FileText size={22} />
            </div>
            <div>
              <h3 className="font-semibold text-white">
                Data export and reporting
              </h3>
              <p className="mt-1 text-sm text-slate-400">
                Download a CSV snapshot of current customer records.
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-medium text-white">
                  Customer data report (.csv)
                </p>
                <p className="mt-1 text-sm text-slate-400">
                  Includes available customer fields and recorded churn labels.
                </p>
              </div>

              <button
                type="button"
                className={button}
                onClick={downloadReport}
                disabled={reportLoading}
              >
                {reportLoading ? (
                  <LoaderCircle size={16} className="animate-spin" />
                ) : (
                  <Download size={16} />
                )}
                Download CSV
              </button>
            </div>

            {reportMessage && (
              <p className="mt-4 text-sm text-slate-300">
                {reportMessage}
              </p>
            )}
          </div>

          <div className="mt-4 flex items-start gap-2 text-xs leading-5 text-slate-500">
            <ShieldCheck size={16} className="mt-0.5 shrink-0" />
            Store exported customer information securely.
          </div>
        </section>
      )}

      {tab === "alerts" && (
        <div className="space-y-5">
          <section className={panel}>
            <div className="mb-5 flex items-center gap-3">
              <div className="rounded-xl bg-amber-500/10 p-3 text-amber-300">
                <Activity size={22} />
              </div>
              <div>
                <h3 className="font-semibold text-white">
                  Monitoring thresholds
                </h3>
                <p className="mt-1 text-sm text-slate-400">
                  Configure when the API should flag observed churn metrics.
                </p>
              </div>
            </div>

            <form
              onSubmit={saveAlerts}
              className="grid gap-4 md:grid-cols-3"
            >
              <label className="text-sm text-slate-300">
                Churn-rate threshold (%)
                <input
                  className={`${input} mt-2`}
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={alertSettings.churn_rate_threshold}
                  onChange={(event) =>
                    setAlertSettings({
                      ...alertSettings,
                      churn_rate_threshold: event.target.value,
                    })
                  }
                  required
                />
              </label>

              <label className="text-sm text-slate-300">
                Minimum segment size
                <input
                  className={`${input} mt-2`}
                  type="number"
                  min="1"
                  step="1"
                  value={alertSettings.minimum_segment_size}
                  onChange={(event) =>
                    setAlertSettings({
                      ...alertSettings,
                      minimum_segment_size: event.target.value,
                    })
                  }
                  required
                />
              </label>

              <label className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={alertSettings.enabled}
                  onChange={(event) =>
                    setAlertSettings({
                      ...alertSettings,
                      enabled: event.target.checked,
                    })
                  }
                  className="h-4 w-4 accent-blue-500"
                />
                Enable churn-rate alerts
              </label>

              <div className="flex flex-wrap gap-2 md:col-span-3">
                <button
                  type="submit"
                  className={button}
                  disabled={alertLoading}
                >
                  {alertLoading ? (
                    <LoaderCircle size={16} className="animate-spin" />
                  ) : (
                    <CheckCircle2 size={16} />
                  )}
                  Save settings
                </button>

                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-2.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
                  onClick={evaluateAlerts}
                  disabled={alertLoading}
                >
                  {alertLoading ? (
                    <LoaderCircle size={16} className="animate-spin" />
                  ) : (
                    <Activity size={16} />
                  )}
                  Evaluate now
                </button>

                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-2.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
                  onClick={loadAlertHistory}
                  disabled={historyLoading || alertLoading}
                >
                  <RefreshCw
                    size={16}
                    className={historyLoading ? "animate-spin" : ""}
                  />
                  {historyLoading ? "Refreshing..." : "Refresh history"}
                </button>
              </div>
            </form>

            {alertMessage && (
              <p className="mt-4 text-sm text-emerald-300">
                {alertMessage}
              </p>
            )}

            {alertError && (
              <div className="mt-4">
                <ErrorMessage>{alertError}</ErrorMessage>
              </div>
            )}

            <p className="mt-4 text-xs leading-5 text-amber-300/80">
              The backend records alert history locally. Email or Slack
              delivery requires a configured notification integration.
            </p>
          </section>

          {alerts && (
            <section className={panel}>
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-semibold text-white">
                  Evaluation result
                </h3>
                <span className="text-xs text-slate-500">
                  {alerts.evaluated_at
                    ? new Date(alerts.evaluated_at).toLocaleString()
                    : ""}
                </span>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <Metric
                  label="Observed churn rate"
                  value={`${Number(
                    alerts.summary?.churn_rate || 0
                  ).toFixed(2)}%`}
                />
                <Metric
                  label="Triggered alerts"
                  value={alerts.alerts?.length || 0}
                />
                <Metric
                  label="Customers checked"
                  value={number(alerts.summary?.total_customers)}
                />
              </div>

              {alerts.alerts?.length ? (
                <div className="mt-4 space-y-3">
                  {alerts.alerts.map((alert, index) => (
                    <div
                      key={`${alert.metric}-${index}`}
                      className="rounded-xl border border-amber-800/70 bg-amber-950/20 p-4"
                    >
                      <p className="font-medium text-amber-200">
                        {alert.severity?.toUpperCase()} ·{" "}
                        {alert.metric?.replaceAll("_", " ")}
                      </p>
                      <p className="mt-1 text-sm leading-6 text-slate-300">
                        {alert.message}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-4 flex items-center gap-2 rounded-xl border border-emerald-900 bg-emerald-950/20 p-4 text-sm text-emerald-300">
                  <CheckCircle2 size={17} />
                  No alert thresholds were triggered in this evaluation.
                </p>
              )}
            </section>
          )}

          <section className={panel}>
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-semibold text-white">
                Recent monitoring history
              </h3>
              <span className="text-xs text-slate-500">
                Up to 20 snapshots
              </span>
            </div>

            {historyUpdatedAt && (
              <p className="mt-2 text-xs text-emerald-300">
                History refreshed at{" "}
                {historyUpdatedAt.toLocaleTimeString()}
              </p>
            )}

            {historyLoading && (
              <p className="mt-4 flex items-center gap-2 text-sm text-slate-400">
                <LoaderCircle size={16} className="animate-spin" />
                Loading monitoring history...
              </p>
            )}

            {alertHistory.length > 0 ? (
              <div className="mt-4 space-y-3">
                {alertHistory.map((entry, index) => (
                  <div
                    key={`${entry.evaluated_at}-${index}`}
                    className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">
                        {entry.source === "scheduled"
                          ? "Scheduled check"
                          : "Manual evaluation"}
                      </span>
                      <span className="text-xs text-slate-500">
                        {entry.evaluated_at
                          ? new Date(entry.evaluated_at).toLocaleString()
                          : "Timestamp unavailable"}
                      </span>
                    </div>

                    <p className="mt-2 text-sm text-slate-300">
                      {number(entry.summary?.total_customers)} customers ·{" "}
                      {Number(entry.summary?.churn_rate || 0).toFixed(2)}%
                      {" "}observed churn · {entry.alerts?.length || 0} alert(s)
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              !historyLoading && (
                <p className="mt-3 text-sm text-slate-400">
                  No monitoring history has been recorded yet. Select
                  “Evaluate now” or wait for the scheduled monitor.
                </p>
              )
            )}
          </section>
        </div>
      )}

      <p className="text-xs leading-5 text-slate-500">
        Data source: Spring Boot / MySQL. The current model's ROC-AUC
        is near 0.50, so results should be treated as descriptive
        analytics rather than authoritative churn predictions.
      </p>
    </div>
  );
}