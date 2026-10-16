import { useEffect, useState } from "react";
import { fetchAPI } from "../api";

import {
  Filter,
  RotateCcw,
  Users,
  TrendingDown,
  UserCheck,
  Activity,
  Wifi,
  MapPin,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  AlertCircle,
  RefreshCw,
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

const MIN_SAMPLE_SIZE = 30;

/* Standardize aliases for the same telecom provider. */
function normalizePartnerName(value) {
  const name = String(value ?? "").trim().replace(/\s+/g, " ");
  const normalized = name.toLowerCase().replace(/[.\s_-]+/g, "");

  if (["jio", "reliancejio"].includes(normalized)) {
    return "Reliance Jio";
  }

  if (
    ["vi", "vodafone", "vodafoneidea", "vodafoneindia"].includes(
      normalized
    )
  ) {
    return "Vi";
  }

  if (normalized === "airtel") return "Airtel";
  if (normalized === "bsnl") return "BSNL";

  return name || "Unknown";
}

/* Read either supported backend field format. */
function getCustomers(item) {
  return Number(item?.customers ?? item?.total_customers ?? 0);
}

function getChurned(item) {
  return Number(item?.churned ?? item?.churned_customers ?? 0);
}

/* Merge aliases and calculate rates from the combined counts. */
function mergePartnerStats(items = []) {
  const grouped = new Map();

  for (const item of items) {
    const name = normalizePartnerName(item.telecom_partner);

    const existing = grouped.get(name) ?? {
      telecom_partner: name,
      customers: 0,
      churned: 0,
    };

    existing.customers += getCustomers(item);
    existing.churned += getChurned(item);

    grouped.set(name, existing);
  }

  return [...grouped.values()]
    .map((item) => ({
      ...item,
      churn_rate:
        item.customers > 0
          ? Number(((item.churned / item.customers) * 100).toFixed(2))
          : 0,
    }))
    .sort((a, b) => b.churn_rate - a.churn_rate);
}

/* Merge state or partner rows using their actual name field. */
function normalizeStats(items = [], nameKey) {
  if (nameKey === "telecom_partner") {
    return mergePartnerStats(items);
  }

  return items.map((item) => ({
    ...item,
    customers: getCustomers(item),
    churned: getChurned(item),
    churn_rate: Number(item.churn_rate ?? 0),
  }));
}

function Card({
  title,
  value,
  subtitle,
  icon: Icon,
  color = "bg-blue-500/10 text-blue-400",
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm text-slate-400">{title}</p>
          <h3 className="mt-3 break-words text-2xl font-bold text-white">
            {value ?? "N/A"}
          </h3>
          <p className="mt-2 text-xs leading-5 text-slate-500">
            {subtitle}
          </p>
        </div>

        <div className={`rounded-xl p-3 ${color}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}

function Heading({ icon: Icon, title, description }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2">
        <Icon size={20} className="text-blue-400" />
        <h3 className="font-semibold text-white">{title}</h3>
      </div>

      <p className="mt-2 text-sm leading-6 text-slate-400">
        {description}
      </p>
    </div>
  );
}

const fmt = (value) => Number(value ?? 0).toLocaleString("en-IN");

const rate = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "0.00";
};

function getHighest(items) {
  if (!items.length) return null;

  return items.reduce((best, item) =>
    Number(item.churn_rate) > Number(best.churn_rate) ? item : best
  );
}

function getLowest(items) {
  if (!items.length) return null;

  return items.reduce((best, item) =>
    Number(item.churn_rate) < Number(best.churn_rate) ? item : best
  );
}

function SampleWarning({ customers }) {
  if (Number(customers) >= MIN_SAMPLE_SIZE) return null;

  return (
    <span className="mt-1 inline-flex items-center gap-1 text-xs text-amber-300">
      <AlertCircle size={13} />
      Small sample: {fmt(customers)} customers
    </span>
  );
}

function ComparisonNotice({ count, type }) {
  if (count > 1) return null;

  return (
    <div className="mb-4 flex items-start gap-2 rounded-xl border border-slate-700 bg-slate-950 p-3 text-sm text-slate-400">
      <Info size={17} className="mt-0.5 shrink-0 text-blue-400" />
      <p>
        {count === 0
          ? `No ${type.toLowerCase()} groups are available for comparison with these filters.`
          : `Only one ${type.toLowerCase()} group matches these filters. Highest and lowest rates are identical, so a cross-group comparison is not available.`}
      </p>
    </div>
  );
}

function StatsTable({ items, nameKey, nameLabel }) {
  if (!items.length) {
    return (
      <p className="text-sm text-slate-400">
        No data matches these filters.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[480px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-800 text-slate-400">
            <th className="px-3 py-3">{nameLabel}</th>
            <th className="px-3 py-3 text-right">Customers</th>
            <th className="px-3 py-3 text-right">Churned</th>
            <th className="px-3 py-3 text-right">Observed Rate</th>
          </tr>
        </thead>

        <tbody>
          {items.map((item) => (
            <tr
              key={item[nameKey]}
              className="border-b border-slate-800/70"
            >
              <td className="px-3 py-4 font-medium text-white">
                <div>{item[nameKey]}</div>
                <SampleWarning customers={item.customers} />
              </td>

              <td className="px-3 py-4 text-right">
                {fmt(item.customers)}
              </td>

              <td className="px-3 py-4 text-right">
                {fmt(item.churned)}
              </td>

              <td className="px-3 py-4 text-right text-blue-300">
                {rate(item.churn_rate)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function BusinessInsights() {
  const [partner, setPartner] = useState("");
  const [state, setState] = useState("");
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadInsights() {
      setBusy(true);
      setError("");

      try {
        const params = new URLSearchParams();

        if (partner) {
          params.set("telecom_partner", normalizePartnerName(partner));
        }

        if (state) {
          params.set("state", state);
        }

        const query = params.toString();

        const result = await fetchAPI(
          `/api/business-insights/filtered${query ? `?${query}` : ""}`
        );

        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        console.error("Business insights error:", err);

        if (!cancelled) {
          setError(
            "Could not load business insights. Check that FastAPI, Spring Boot, and MySQL are running, then retry."
          );
        }
      } finally {
        if (!cancelled) {
          setBusy(false);
        }
      }
    }

    loadInsights();

    return () => {
      cancelled = true;
    };
  }, [partner, state, retryCount]);

  const summary = data?.summary;

  const partners = normalizeStats(
    data?.partner_stats ?? [],
    "telecom_partner"
  );

  const states = normalizeStats(data?.state_stats ?? [], "state");

  const stateInsights = data?.state_insights ?? {};

  const highestPartnerRow = getHighest(partners);
  const lowestPartnerRow = getLowest(partners);

  const highestStateRow = getHighest(states);
  const lowestStateRow = getLowest(states);

  /*
   * Use the same merged rows for the partner cards, chart, and table.
   * This prevents unmerged backend insights from showing inconsistent
   * names, counts, or rates.
   */
  const highestPartner = highestPartnerRow?.telecom_partner ?? "N/A";
  const lowestPartner = lowestPartnerRow?.telecom_partner ?? "N/A";

  const highestPartnerRate = highestPartnerRow?.churn_rate ?? 0;
  const lowestPartnerRate = lowestPartnerRow?.churn_rate ?? 0;

  const highestState =
    stateInsights.highest_churn_state ??
    highestStateRow?.state ??
    "N/A";

  const lowestState =
    stateInsights.lowest_churn_state ??
    lowestStateRow?.state ??
    "N/A";

  const highestStateRate =
    stateInsights.highest_churn_rate ??
    highestStateRow?.churn_rate ??
    0;

  const lowestStateRate =
    stateInsights.lowest_churn_rate ??
    lowestStateRow?.churn_rate ??
    0;

  const availablePartners = [
    ...new Set(
      [
        ...(data?.filters?.telecom_partners ?? []),
        ...partners.map((item) => item.telecom_partner).filter(Boolean),
      ].map(normalizePartnerName)
    ),
  ].sort((a, b) => a.localeCompare(b));

  const availableStates = [
    ...new Set([
      ...(data?.available_states ?? data?.filters?.states ?? []),
      ...states.map((item) => item.state).filter(Boolean),
    ]),
  ].sort();

  function resetFilters() {
    setPartner("");
    setState("");
  }

  function retryLoading() {
    setRetryCount((count) => count + 1);
  }

  return (
    <div className="space-y-7">
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5 md:p-6">
        <Heading
          icon={Filter}
          title="Filter Business Insights"
          description="Select a telecom partner, a state, or both. Metrics and tables update for matching customer records."
        />

        <div className="grid gap-4 md:grid-cols-3">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-200">
              Telecom Partner
            </span>

            <select
              value={partner}
              onChange={(event) => setPartner(event.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
            >
              <option value="">All telecom partners</option>
              {availablePartners.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-200">
              State
            </span>

            <select
              value={state}
              onChange={(event) => setState(event.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
            >
              <option value="">All states</option>
              {availableStates.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <div className="flex items-end">
            <button
              type="button"
              onClick={resetFilters}
              disabled={(!partner && !state) || busy}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RotateCcw size={16} />
              Reset Filters
            </button>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          {partner && (
            <span className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs text-blue-300">
              Partner: {partner}
            </span>
          )}

          {state && (
            <span className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs text-blue-300">
              State: {state}
            </span>
          )}

          {busy && (
            <span role="status" className="text-xs text-blue-300">
              Updating metrics…
            </span>
          )}

          {data?.data_source && (
            <span className="ml-auto rounded-lg border border-emerald-900 bg-emerald-950/30 px-3 py-1.5 text-xs text-emerald-300">
              Source: {data.data_source.toUpperCase()}
            </span>
          )}
        </div>
      </section>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-amber-900 bg-amber-950/30 p-4 text-sm text-amber-200"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="flex items-start gap-2">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              {error}
            </p>

            <button
              type="button"
              onClick={retryLoading}
              disabled={busy}
              className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-amber-800 px-3 py-2 font-medium hover:bg-amber-900/40 disabled:opacity-50"
            >
              <RefreshCw size={15} />
              Retry
            </button>
          </div>
        </div>
      )}

      {busy && !data && !error && (
        <div
          role="status"
          className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-400"
        >
          Loading business insights…
        </div>
      )}

      {!busy && !error && data && !summary && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-400">
          The API response did not include summary metrics.
          <button
            type="button"
            onClick={retryLoading}
            className="ml-2 underline underline-offset-4"
          >
            Try again
          </button>
        </div>
      )}

      {summary && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card
              title="Total Customers"
              value={fmt(summary.total_customers)}
              subtitle="Customers matching selected filters"
              icon={Users}
            />

            <Card
              title="Recorded Churn"
              value={fmt(summary.churned_customers)}
              subtitle="Matching customers marked as churned"
              icon={TrendingDown}
              color="bg-rose-500/10 text-rose-400"
            />

            <Card
              title="Retained Customers"
              value={fmt(summary.non_churned_customers)}
              subtitle="Matching customers not marked as churned"
              icon={UserCheck}
              color="bg-emerald-500/10 text-emerald-400"
            />

            <Card
              title="Observed Churn Rate"
              value={`${rate(summary.churn_rate)}%`}
              subtitle="Churned share of filtered customers"
              icon={Activity}
              color="bg-amber-500/10 text-amber-400"
            />
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5 md:p-6">
            <Heading
              icon={Wifi}
              title="Telecom Partner Insights"
              description={`Partner statistics for ${
                partner || "all partners"
              }${state ? ` in ${state}` : ""}.`}
            />

            <ComparisonNotice count={partners.length} type="Partner" />

            <div className="grid gap-4 md:grid-cols-2">
              <Card
                title="Highest observed partner rate"
                value={highestPartner}
                subtitle={
                  highestPartnerRow
                    ? `${rate(highestPartnerRate)}% churn · ${fmt(
                        highestPartnerRow.customers
                      )} customers`
                    : "No partner data available"
                }
                icon={ArrowUpRight}
                color="bg-rose-500/10 text-rose-400"
              />

              <Card
                title="Lowest observed partner rate"
                value={lowestPartner}
                subtitle={
                  lowestPartnerRow
                    ? `${rate(lowestPartnerRate)}% churn · ${fmt(
                        lowestPartnerRow.customers
                      )} customers`
                    : "No partner data available"
                }
                icon={ArrowDownRight}
                color="bg-emerald-500/10 text-emerald-400"
              />
            </div>

            {partners.some(
              (item) => Number(item.customers) < MIN_SAMPLE_SIZE
            ) && (
              <div className="mt-4 flex items-start gap-2 rounded-xl border border-amber-900/60 bg-amber-950/20 p-3 text-xs leading-5 text-amber-200">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                Some partner groups have fewer than {MIN_SAMPLE_SIZE}{" "}
                customers. Their observed rates can be unstable; compare
                sample sizes before drawing conclusions.
              </div>
            )}

            {partners.length > 0 && (
              <>
                <div className="mt-7 h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={partners}>
                      <CartesianGrid
                        stroke="#263244"
                        strokeDasharray="3 3"
                        vertical={false}
                      />

                      <XAxis
                        dataKey="telecom_partner"
                        tick={{ fill: "#94A3B8", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                      />

                      <YAxis
                        tick={{ fill: "#94A3B8", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(value) => `${value}%`}
                      />

                      <Tooltip
                        formatter={(value, name, props) => [
                          `${rate(value)}% · ${fmt(
                            props.payload.customers
                          )} customers`,
                          "Observed churn",
                        ]}
                        contentStyle={{
                          backgroundColor: "#111827",
                          border: "1px solid #334155",
                          borderRadius: 12,
                          color: "#F8FAFC",
                        }}
                      />

                      <Bar
                        dataKey="churn_rate"
                        name="Observed churn"
                        fill="#60A5FA"
                        radius={[6, 6, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="mt-5">
                  <StatsTable
                    items={partners}
                    nameKey="telecom_partner"
                    nameLabel="Telecom Partner"
                  />
                </div>
              </>
            )}

            {partners.length === 0 && (
              <p className="text-sm text-slate-400">
                No partner data matches these filters.
              </p>
            )}
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5 md:p-6">
            <Heading
              icon={MapPin}
              title="Geographic Observations"
              description={`State statistics for ${
                partner || "all partners"
              }${state ? ` in ${state}` : ""}.`}
            />

            <ComparisonNotice count={states.length} type="State" />

            <div className="grid gap-4 md:grid-cols-2">
              <Card
                title="Highest observed state rate"
                value={highestState}
                subtitle={
                  highestStateRow
                    ? `${rate(highestStateRate)}% churn · ${fmt(
                        highestStateRow.customers
                      )} customers`
                    : "No state data available"
                }
                icon={ArrowUpRight}
                color="bg-amber-500/10 text-amber-400"
              />

              <Card
                title="Lowest observed state rate"
                value={lowestState}
                subtitle={
                  lowestStateRow
                    ? `${rate(lowestStateRate)}% churn · ${fmt(
                        lowestStateRow.customers
                      )} customers`
                    : "No state data available"
                }
                icon={ArrowDownRight}
                color="bg-emerald-500/10 text-emerald-400"
              />
            </div>

            {states.some(
              (item) => Number(item.customers) < MIN_SAMPLE_SIZE
            ) && (
              <div className="mt-4 flex items-start gap-2 rounded-xl border border-amber-900/60 bg-amber-950/20 p-3 text-xs leading-5 text-amber-200">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                Some state groups have fewer than {MIN_SAMPLE_SIZE}{" "}
                customers. Their observed rates can be unstable; interpret
                them alongside customer counts.
              </div>
            )}

            <div className="mt-5">
              <StatsTable
                items={states}
                nameKey="state"
                nameLabel="State"
              />
            </div>

            <div className="mt-5 flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-950 p-4">
              <Info
                size={18}
                className="mt-0.5 shrink-0 text-blue-400"
              />

              <p className="text-xs leading-6 text-slate-400">
                These values describe recorded churn rates, not causes of
                churn. Small groups can produce extreme rates from only a
                few records. Interpret comparisons alongside customer counts
                and data quality.
              </p>
            </div>
          </section>

          <section className="rounded-2xl border border-amber-900/60 bg-amber-950/20 p-5">
            <div className="flex items-start gap-3">
              <AlertCircle
                size={20}
                className="mt-0.5 shrink-0 text-amber-400"
              />

              <div>
                <h3 className="font-semibold text-amber-300">
                  Interpretation and model limitations
                </h3>

                <p className="mt-2 text-sm leading-6 text-amber-100/80">
                  These charts summarize observed patterns in the available
                  customer data. They do not establish causation. The current
                  churn prediction model has limited discriminatory power,
                  so its output should not be used as the sole basis for
                  customer-retention decisions.
                </p>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}