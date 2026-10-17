import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import ChurnAnalysis from "./pages/ChurnAnalysis";
import ChurnPrediction from "./pages/ChurnPrediction";
import Customers from "./components/Customers";
import BusinessInsights from "./pages/BusinessInsights";
import Intelligence from "./pages/Intelligence";
import { fetchAPI } from "./api";

import {
  LayoutDashboard,
  Users,
  TrendingDown,
  UserCheck,
  Activity,
  RefreshCw,
  AlertCircle,
  Wifi,
  BarChart3,
  BrainCircuit,
  ArrowUpRight,
  ArrowDownRight,
  MapPin,
  Info,
  Sparkles,
} from "lucide-react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

const navigation = [
  { label: "Overview", icon: LayoutDashboard, path: "/" },
  { label: "Customers", icon: Users, path: "/customers" },
  { label: "Churn Analysis", icon: TrendingDown, path: "/churn-analysis" },
  { label: "Business Insights", icon: Activity, path: "/business-insights" },
  { label: "Churn Prediction", icon: BrainCircuit, path: "/churn-prediction" },
  { label: "AI Intelligence", icon: Sparkles, path: "/intelligence" },
];

const pageFromPath = {
  "/": "Overview",
  "/customers": "Customers",
  "/churn-analysis": "Churn Analysis",
  "/business-insights": "Business Insights",
  "/churn-prediction": "Churn Prediction",
  "/intelligence": "AI Intelligence",
};

// Standardize aliases before combining partner statistics.
function normalizePartnerName(value) {
  const name = String(value ?? "").trim().replace(/\s+/g, " ");
  const normalized = name.toLowerCase().replace(/[.\s_-]+/g, "");

  if (["jio", "reliancejio"].includes(normalized)) {
    return "Reliance Jio";
  }

  if (
    ["vi", "vodafone", "vodafoneidea", "vodafoneindia"].includes(normalized)
  ) {
    return "Vi";
  }

  if (normalized === "airtel") return "Airtel";
  if (normalized === "bsnl") return "BSNL";

  return name;
}

function normalizePartnerStats(items) {
  const grouped = new Map();

  for (const item of items) {
    const telecom_partner = normalizePartnerName(item.telecom_partner);

    if (!telecom_partner) continue;

    const customers = Number(
      item.total_customers ?? item.customers ?? 0
    );

    const churned = Number(
      item.churned_customers ?? item.churned ?? 0
    );

    const existing = grouped.get(telecom_partner) ?? {
      telecom_partner,
      customers: 0,
      churned: 0,
    };

    existing.customers += Number.isFinite(customers) ? customers : 0;
    existing.churned += Number.isFinite(churned) ? churned : 0;

    grouped.set(telecom_partner, existing);
  }

  return [...grouped.values()]
    .map((item) => ({
      ...item,
      total_customers: item.customers,
      churned_customers: item.churned,
      churn_rate:
        item.customers > 0
          ? Number(((item.churned / item.customers) * 100).toFixed(2))
          : 0,
    }))
    .sort((a, b) =>
      a.telecom_partner.localeCompare(b.telecom_partner)
    );
}

function StatCard({ title, value, subtitle, icon: Icon, color }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 transition hover:border-slate-700">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm text-slate-400">{title}</p>

          <h2 className="mt-3 break-words text-3xl font-bold tracking-tight text-white">
            {value}
          </h2>

          <p className="mt-2 text-xs leading-5 text-slate-500">
            {subtitle}
          </p>
        </div>

        <div className={`shrink-0 rounded-xl p-3 ${color}`}>
          <Icon size={21} />
        </div>
      </div>
    </div>
  );
}

function InsightCard({ title, value, subtitle, icon: Icon, color }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-5 transition hover:border-slate-700">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm text-slate-400">{title}</p>

          <h3 className="mt-3 break-words text-xl font-bold text-white">
            {value}
          </h3>

          <p className="mt-2 text-xs leading-5 text-slate-500">
            {subtitle}
          </p>
        </div>

        <div className={`shrink-0 rounded-xl p-3 ${color}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}

function SectionHeading({ icon: Icon, title, description }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2">
        <Icon size={20} className="shrink-0 text-blue-400" />
        <h3 className="font-semibold text-white">{title}</h3>
      </div>

      <p className="mt-2 text-sm leading-6 text-slate-400">
        {description}
      </p>
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/60 px-5 py-10 text-center">
      <Info size={22} className="mx-auto text-slate-500" />

      <p className="mt-3 text-sm text-slate-400">{message}</p>
    </div>
  );
}

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const activePage = pageFromPath[location.pathname] || "Overview";

  const [summary, setSummary] = useState(null);
  const [partners, setPartners] = useState([]);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [insightsError, setInsightsError] = useState("");

  const formatNumber = (n) =>
    Number(n ?? 0).toLocaleString("en-IN");

  const formatRate = (n) => {
    const value = Number(n);
    return Number.isFinite(value) ? value.toFixed(2) : "0.00";
  };

  const pageDescriptions = {
    Overview: "Understand customer retention and observed churn patterns.",
    Customers: "Search, filter, and explore customer records.",
    "Churn Analysis":
      "Explore observed churn patterns across telecom partners.",
    "Business Insights":
      "Explore customer trends and descriptive business metrics.",
    "Churn Prediction":
      "Estimate customer churn risk using account and usage details.",
    "AI Intelligence":
      "Ask grounded data questions, investigate segments, export reports, and evaluate monitoring thresholds.",
  };

  async function loadDashboard() {
    try {
      const [summaryResult, partnerResult, insightsResult] =
        await Promise.allSettled([
          fetchAPI("/api/summary"),
          fetchAPI("/api/churn-by-partner"),
          fetchAPI("/api/business-insights"),
        ]);

      if (summaryResult.status === "fulfilled") {
        setSummary(summaryResult.value);
        setError("");
      } else {
        setSummary(null);

        setError(
          "Summary data could not be loaded. Check the FastAPI terminal for the /api/summary error."
        );

        console.error("Summary API error:", summaryResult.reason);
      }

      if (partnerResult.status === "fulfilled") {
        const result = partnerResult.value;

        const rows = Array.isArray(result)
          ? result
          : Array.isArray(result?.value)
            ? result.value
            : [];

        setPartners(normalizePartnerStats(rows));
      } else {
        setPartners([]);
        console.error(
          "Churn-by-partner API error:",
          partnerResult.reason
        );
      }

      if (insightsResult.status === "fulfilled") {
        setInsights(insightsResult.value);
        setInsightsError("");
      } else {
        setInsights(null);

        setInsightsError(
          "Business insights are not available. Check the backend API."
        );

        console.error(
          "Business insights API error:",
          insightsResult.reason
        );
      }
    } catch (err) {
      console.error("Dashboard loading error:", err);

      setError(
        "An unexpected error occurred while loading the dashboard."
      );
    } finally {
      setLoading(false);
    }
  }

  // Schedule the initial request outside the synchronous effect body.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadDashboard();
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  const sortedOverviewPartners = [...partners].sort(
    (a, b) => Number(b.churn_rate ?? 0) - Number(a.churn_rate ?? 0)
  );

  const partnerInsights = insights?.partner_insights;
  const stateInsights = insights?.state_insights;

  const highestPartner =
    partnerInsights?.highest_churn_telecom_partner ??
    partnerInsights?.highest_churn_partner ??
    sortedOverviewPartners[0]?.telecom_partner ??
    "N/A";

  const lowestPartner =
    partnerInsights?.lowest_churn_telecom_partner ??
    partnerInsights?.lowest_churn_partner ??
    sortedOverviewPartners[sortedOverviewPartners.length - 1]
      ?.telecom_partner ??
    "N/A";

  const highestPartnerRate =
    partnerInsights?.highest_churn_rate ??
    sortedOverviewPartners[0]?.churn_rate ??
    0;

  const lowestPartnerRate =
    partnerInsights?.lowest_churn_rate ??
    sortedOverviewPartners[sortedOverviewPartners.length - 1]
      ?.churn_rate ??
    0;

  const handleRefresh = () => {
    setLoading(true);
    setError("");
    setInsightsError("");

    void loadDashboard();
  };

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100 md:flex">
      <aside className="border-b border-slate-800 bg-slate-900 p-5 md:min-h-screen md:w-64 md:shrink-0 md:border-b-0 md:border-r">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-600 p-2.5">
            <Activity size={24} />
          </div>

          <div>
            <h1 className="font-bold text-white">Aveniq</h1>
            <p className="text-xs text-slate-400">
              Customer Intelligence
            </p>
          </div>
        </div>

        <p className="mb-3 mt-9 text-xs font-semibold uppercase tracking-widest text-slate-500">
          Workspace
        </p>

        <nav className="flex gap-2 overflow-x-auto md:flex-col">
          {navigation.map(({ label, icon: Icon, path }) => (
            <button
              key={label}
              onClick={() => {
                navigate(path);
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
              className={`flex shrink-0 items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${
                activePage === label
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>

        <div className="mt-8 hidden rounded-xl border border-slate-800 bg-slate-950 p-4 md:block">
          <div className="flex items-center gap-2 text-sm text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Analytics workspace
          </div>

          <p className="mt-2 text-xs leading-5 text-slate-500">
            Insights are calculated from the cleaned customer dataset.
          </p>
        </div>
      </aside>

      <main className="min-w-0 flex-1 p-5 md:p-8 lg:p-10">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-blue-400">
              ANALYTICS / {activePage.toUpperCase()}
            </p>

            <h2 className="mt-2 text-2xl font-bold text-white md:text-3xl">
              {activePage === "Overview"
                ? "Customer Churn Dashboard"
                : activePage}
            </h2>

            <p className="mt-2 text-sm text-slate-400">
              {pageDescriptions[activePage]}
            </p>
          </div>

          {activePage !== "Customers" && (
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-200 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw
                size={16}
                className={loading ? "animate-spin" : ""}
              />

              {loading ? "Refreshing..." : "Refresh data"}
            </button>
          )}
        </header>

        {error && (
          <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-300">
            <AlertCircle size={20} className="shrink-0" />

            <div>
              <p className="font-semibold">Connection error</p>
              <p className="mt-1">{error}</p>

              <button
                onClick={handleRefresh}
                disabled={loading}
                className="mt-3 rounded-lg border border-red-800 px-3 py-1.5 text-xs font-medium hover:bg-red-900/40 disabled:opacity-50"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {loading && !summary && activePage !== "Customers" && (
          <div className="mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">
            Loading customer analytics...
          </div>
        )}

        {activePage === "Customers" ? (
          <Customers />
        ) : activePage === "Churn Analysis" ? (
          <ChurnAnalysis />
        ) : activePage === "Churn Prediction" ? (
          <ChurnPrediction />
        ) : activePage === "Business Insights" ? (
          <BusinessInsights />
        ) : activePage === "AI Intelligence" ? (
          <Intelligence />
        ) : (
          <>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <StatCard
                title="Total Customers"
                value={formatNumber(summary?.total_customers)}
                subtitle="Customers in the dataset"
                icon={Users}
                color="bg-blue-500/10 text-blue-400"
              />

              <StatCard
                title="Churned Customers"
                value={formatNumber(summary?.churned_customers)}
                subtitle="Recorded churn cases"
                icon={TrendingDown}
                color="bg-rose-500/10 text-rose-400"
              />

              <StatCard
                title="Retained Customers"
                value={formatNumber(summary?.non_churned_customers)}
                subtitle="Recorded non-churn cases"
                icon={UserCheck}
                color="bg-emerald-500/10 text-emerald-400"
              />

              <StatCard
                title="Overall Churn Rate"
                value={`${formatRate(summary?.churn_rate)}%`}
                subtitle="Share of customers marked churned"
                icon={Activity}
                color="bg-amber-500/10 text-amber-400"
              />
            </section>

            <section className="mt-7 grid gap-6 xl:grid-cols-3">
              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 xl:col-span-2 md:p-6">
                <SectionHeading
                  icon={BarChart3}
                  title="Churn by Telecom Partner"
                  description="Compare recorded churn rates across telecom providers."
                />

                {sortedOverviewPartners.length ? (
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={sortedOverviewPartners}>
                        <CartesianGrid
                          stroke="#263244"
                          strokeDasharray="3 3"
                          vertical={false}
                        />

                        <XAxis
                          dataKey="telecom_partner"
                          tick={{ fill: "#94A3B8", fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                        />

                        <YAxis
                          tick={{ fill: "#94A3B8", fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                          tickFormatter={(value) => `${value}%`}
                        />

                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#111827",
                            border: "1px solid #334155",
                            borderRadius: "12px",
                            color: "#F8FAFC",
                          }}
                          formatter={(value, name, props) => [
                            `${formatRate(value)}% · ${formatNumber(
                              props.payload.customers
                            )} customers`,
                            "Observed churn rate",
                          ]}
                        />

                        <Bar
                          dataKey="churn_rate"
                          fill="#60A5FA"
                          radius={[6, 6, 0, 0]}
                          maxBarSize={58}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <EmptyState message="No telecom partner data is available." />
                )}
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 md:p-6">
                <SectionHeading
                  icon={Wifi}
                  title="Partner Breakdown"
                  description="Customer counts and recorded churn rates by provider."
                />

                <div className="space-y-4">
                  {sortedOverviewPartners.map((item) => (
                    <div
                      key={item.telecom_partner}
                      className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium text-white">
                          {item.telecom_partner}
                        </span>

                        <span className="font-semibold text-blue-300">
                          {formatRate(item.churn_rate)}%
                        </span>
                      </div>

                      <p className="mt-2 text-xs text-slate-400">
                        {formatNumber(item.customers)} customers ·{" "}
                        {formatNumber(item.churned)} churned
                      </p>
                    </div>
                  ))}

                  {!sortedOverviewPartners.length && (
                    <p className="text-sm text-slate-500">
                      No partner data is available.
                    </p>
                  )}
                </div>
              </div>
            </section>

            <section className="mt-7 rounded-2xl border border-slate-800 bg-slate-900 p-5 md:p-6">
              <SectionHeading
                icon={Activity}
                title="Business Insights"
                description="A summary of observed patterns in the customer dataset."
              />

              {insights ? (
                <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                  <InsightCard
                    title="Highest observed partner churn"
                    value={highestPartner}
                    subtitle={`${formatRate(highestPartnerRate)}% recorded churn rate`}
                    icon={ArrowUpRight}
                    color="bg-rose-500/10 text-rose-400"
                  />

                  <InsightCard
                    title="Lowest observed partner churn"
                    value={lowestPartner}
                    subtitle={`${formatRate(lowestPartnerRate)}% recorded churn rate`}
                    icon={ArrowDownRight}
                    color="bg-emerald-500/10 text-emerald-400"
                  />

                  <InsightCard
                    title="Highest observed state rate"
                    value={stateInsights?.highest_churn_state ?? "N/A"}
                    subtitle={`${formatRate(stateInsights?.highest_churn_rate)}% recorded churn rate`}
                    icon={MapPin}
                    color="bg-amber-500/10 text-amber-400"
                  />
                </div>
              ) : (
                <EmptyState
                  message={
                    insightsError ||
                    "Business insights are not available yet."
                  }
                />
              )}
            </section>

            <footer className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-5 text-xs text-slate-500">
              <span>Customer Churn Intelligence Platform</span>

              <span>
                Data-driven insights · Predictive model limitations disclosed
              </span>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}

export default App;