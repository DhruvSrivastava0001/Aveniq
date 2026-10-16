
import { useCallback, useEffect, useState } from "react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LabelList,
} from "recharts";

import {
  Users,
  MapPin,
  CalendarDays,
  TrendingDown,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

import { fetchAPI } from "../api";

const chartConfigs = [
  {
    title: "Churn by Gender",
    subtitle: "Observed churn rate across gender groups",
    endpoint: "/api/churn-by-gender",
    labelKey: "gender",
    color: "#60A5FA",
    icon: Users,
  },
  {
    title: "Churn by Age Group",
    subtitle: "Compare observed churn rates across age groups",
    endpoint: "/api/churn-by-age-group",
    labelKey: "age_group",
    color: "#A78BFA",
    icon: TrendingDown,
  },
  {
    title: "Churn by Tenure",
    subtitle: "Compare churn rates by customer tenure",
    endpoint: "/api/churn-by-tenure",
    labelKey: "tenure_group",
    color: "#34D399",
    icon: CalendarDays,
  },
  {
    title: "Churn by State",
    subtitle: "Compare observed churn rates across states",
    endpoint: "/api/churn-by-state",
    labelKey: "state",
    color: "#FBBF24",
    icon: MapPin,
    horizontal: true,
    limit: 15,
  },
  {
    title: "Churn by City",
    subtitle: "Explore observed churn rates across cities",
    endpoint: "/api/churn-by-city",
    labelKey: "city",
    color: "#F87171",
    icon: MapPin,
    horizontal: true,
    limit: 10,
  },
];

function findField(row, possibleNames) {
  const key = Object.keys(row).find((item) =>
    possibleNames.includes(item.toLowerCase())
  );

  return key ? row[key] : undefined;
}

function formatCount(value) {
  if (value === undefined || value === null || value === "") {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number)
    ? number.toLocaleString("en-IN")
    : String(value);
}

function formatRate(value) {
  const number = Number(value);

  return Number.isFinite(number)
    ? `${number.toFixed(2)}%`
    : "N/A";
}

function ChurnTooltip({ active, payload, label }) {
  if (!active || !payload?.length) {
    return null;
  }

  const row = payload[0].payload;

  const churnRate = findField(row, ["churn_rate", "churnrate"]);
  const customers = findField(row, [
    "customers",
    "customer_count",
    "total_customers",
    "customer_count_total",
  ]);
  const churned = findField(row, [
    "churned",
    "churned_customers",
    "churn_count",
    "churned_count",
  ]);

  return (
    <div className="min-w-48 rounded-xl border border-slate-700 bg-slate-950 p-4 shadow-xl">
      <p className="mb-3 font-semibold text-white">{label}</p>

      {churnRate !== undefined && (
        <p className="mb-2 text-sm text-blue-300">
          Churn rate: {formatRate(churnRate)}
        </p>
      )}

      {customers !== undefined && (
        <p className="mb-2 text-sm text-slate-300">
          Total customers: {formatCount(customers)}
        </p>
      )}

      {churned !== undefined && (
        <p className="text-sm text-slate-300">
          Churned customers: {formatCount(churned)}
        </p>
      )}
    </div>
  );
}

function ChurnChart({ config, data }) {
  const Icon = config.icon;
  const horizontal = Boolean(config.horizontal);

  if (!Array.isArray(data) || data.length === 0) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h3 className="font-semibold text-white">{config.title}</h3>
        <p className="mt-3 text-sm text-slate-400">
          No data is available for this chart.
        </p>
      </section>
    );
  }

  const chartData = [...data]
    .filter((row) => Number.isFinite(Number(row.churn_rate)))
    .sort(
      (a, b) =>
        Number(b.churn_rate) - Number(a.churn_rate)
    )
    .slice(0, config.limit ?? 15);

  const chartHeight = horizontal
    ? Math.max(300, chartData.length * 34 + 35)
    : 300;

  return (
    <section className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900 p-5 md:p-6">
      <div className="mb-5 flex items-start gap-3">
        <div className="shrink-0 rounded-xl bg-slate-800 p-2.5">
          <Icon size={20} style={{ color: config.color }} />
        </div>

        <div className="min-w-0">
          <h3 className="font-semibold text-white">{config.title}</h3>
          <p className="mt-1 text-sm leading-5 text-slate-400">
            {config.subtitle}
          </p>
        </div>
      </div>

      <div className="w-full" style={{ height: chartHeight }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout={horizontal ? "vertical" : "horizontal"}
            margin={
              horizontal
                ? { top: 8, right: 58, left: 8, bottom: 8 }
                : { top: 18, right: 16, left: 0, bottom: 8 }
            }
          >
            <CartesianGrid
              stroke="#263244"
              strokeDasharray="3 3"
              vertical={!horizontal}
              horizontal={horizontal}
            />

            {horizontal ? (
              <>
                <XAxis
                  type="number"
                  domain={[0, 24]}
                  ticks={[0, 6, 12, 18, 24]}
                  tick={{ fill: "#94A3B8", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(value) => `${value}%`}
                />

                <YAxis
                  type="category"
                  dataKey={config.labelKey}
                  width={125}
                  interval={0}
                  reversed
                  tick={{ fill: "#CBD5E1", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
              </>
            ) : (
              <>
                <XAxis
                  type="category"
                  dataKey={config.labelKey}
                  interval={0}
                  tick={{ fill: "#CBD5E1", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  height={45}
                />

                <YAxis
                  type="number"
                  domain={[0, 24]}
                  ticks={[0, 6, 12, 18, 24]}
                  tick={{ fill: "#94A3B8", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(value) => `${value}%`}
                />
              </>
            )}

            <Tooltip
              content={<ChurnTooltip />}
              cursor={{
                fill: "#334155",
                fillOpacity: 0.25,
              }}
            />

            <Bar
              dataKey="churn_rate"
              name="Churn rate"
              fill={config.color}
              radius={horizontal ? [0, 5, 5, 0] : [5, 5, 0, 0]}
              maxBarSize={horizontal ? 22 : 42}
            >
              <LabelList
                dataKey="churn_rate"
                position={horizontal ? "right" : "top"}
                formatter={(value) => formatRate(value)}
                fill="#CBD5E1"
                fontSize={11}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-3 text-xs leading-5 text-slate-500">
        {horizontal
          ? `Showing up to ${config.limit} categories, ordered from highest to lowest observed churn rate.`
          : "Categories are ordered from highest to lowest observed churn rate."}{" "}
        Hover over a bar for the churn rate and available customer counts.
      </p>
    </section>
  );
}

export default function ChurnAnalysis() {
  const [datasets, setDatasets] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAnalysis = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const results = await Promise.all(
        chartConfigs.map(async (config) => {
          const data = await fetchAPI(config.endpoint);

          if (!Array.isArray(data)) {
            throw new Error(
              `Unexpected response from ${config.endpoint}`
            );
          }

          return [config.endpoint, data];
        })
      );

      setDatasets(Object.fromEntries(results));
    } catch (err) {
      console.error("Unable to load churn analysis:", err);

      setError(
        "Unable to load analysis data. Check that FastAPI is running and inspect the endpoint responses in /docs."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Fetch the analytics data when this page mounts.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadAnalysis();
  }, [loadAnalysis]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-white">
            Customer Churn Patterns
          </h3>
          <p className="mt-1 text-sm leading-6 text-slate-400">
            Explore recorded churn rates across customer groups
            and geographic locations.
          </p>
        </div>

        <button
          onClick={loadAnalysis}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-200 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            size={16}
            className={loading ? "animate-spin" : ""}
          />
          {loading ? "Refreshing..." : "Refresh analysis"}
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-300">
          <AlertCircle size={20} className="shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center text-slate-400">
          Loading churn analysis...
        </div>
      ) : (
        <div className="grid min-w-0 grid-cols-1 items-start gap-6 xl:grid-cols-2">
          {chartConfigs.map((config) => (
            <ChurnChart
              key={config.endpoint}
              config={config}
              data={datasets[config.endpoint]}
            />
          ))}
        </div>
      )}

      <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-4">
        <p className="text-sm leading-6 text-amber-200/80">
          These charts describe patterns in the available dataset.
          They do not establish why customers churn, and the
          prediction model has limited discriminatory power.
        </p>
      </div>
    </div>
  );
}

