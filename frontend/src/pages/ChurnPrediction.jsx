
import { useState } from "react";
import { postAPI, postIBMAPI } from "../api";
import {
  BrainCircuit,
  UserRound,
  Activity,
  RotateCcw,
  AlertCircle,
  ShieldAlert,
  CheckCircle2,
  Lightbulb,
} from "lucide-react";

const initialForm = {
  telecom_partner: "Airtel",
  gender: "M",
  age: 30,
  state: "Karnataka",
  city: "Bengaluru",
  num_dependents: 1,
  estimated_salary: 45000,
  calls_made: 100,
  sms_sent: 50,
  data_used: 10,
  tenure_months: 12,
  registration_year: 2023,
};

const initialIBMForm = {
  gender: "Female",
  SeniorCitizen: 0,
  Partner: "Yes",
  Dependents: "No",
  tenure: 12,
  PhoneService: "Yes",
  MultipleLines: "No",
  InternetService: "Fiber optic",
  OnlineSecurity: "No",
  OnlineBackup: "Yes",
  DeviceProtection: "No",
  TechSupport: "No",
  StreamingTV: "Yes",
  StreamingMovies: "Yes",
  Contract: "Month-to-month",
  PaperlessBilling: "Yes",
  PaymentMethod: "Electronic check",
  MonthlyCharges: 85.5,
  TotalCharges: 1026,
};

const fields = [
  { name: "age", label: "Age", min: 0, max: 120 },
  { name: "num_dependents", label: "Number of Dependents", min: 0 },
  { name: "estimated_salary", label: "Estimated Salary", min: 0 },
  { name: "calls_made", label: "Calls Made", min: 0 },
  { name: "sms_sent", label: "SMS Sent", min: 0 },
  { name: "data_used", label: "Data Used", min: 0 },
  { name: "tenure_months", label: "Tenure (Months)", min: 0 },
  {
    name: "registration_year",
    label: "Registration Year",
    min: 2020,
    max: 2023,
  },
];

const ibmFields = [
  {
    name: "gender",
    label: "Gender",
    type: "select",
    options: ["Female", "Male"],
  },
  {
    name: "SeniorCitizen",
    label: "Senior Citizen",
    type: "select",
    options: [
      { label: "No", value: 0 },
      { label: "Yes", value: 1 },
    ],
  },
  { name: "Partner", label: "Has Partner", type: "yesNo" },
  { name: "Dependents", label: "Has Dependents", type: "yesNo" },
  {
    name: "tenure",
    label: "Tenure (Months)",
    type: "number",
    min: 0,
    max: 100,
  },
  { name: "PhoneService", label: "Phone Service", type: "yesNo" },
  {
    name: "MultipleLines",
    label: "Multiple Lines",
    type: "select",
    options: ["No", "Yes", "No phone service"],
  },
  {
    name: "InternetService",
    label: "Internet Service",
    type: "select",
    options: ["DSL", "Fiber optic", "No"],
  },
  {
    name: "OnlineSecurity",
    label: "Online Security",
    type: "select",
    options: ["No", "Yes", "No internet service"],
  },
  {
    name: "OnlineBackup",
    label: "Online Backup",
    type: "select",
    options: ["No", "Yes", "No internet service"],
  },
  {
    name: "DeviceProtection",
    label: "Device Protection",
    type: "select",
    options: ["No", "Yes", "No internet service"],
  },
  {
    name: "TechSupport",
    label: "Tech Support",
    type: "select",
    options: ["No", "Yes", "No internet service"],
  },
  {
    name: "StreamingTV",
    label: "Streaming TV",
    type: "select",
    options: ["No", "Yes", "No internet service"],
  },
  {
    name: "StreamingMovies",
    label: "Streaming Movies",
    type: "select",
    options: ["No", "Yes", "No internet service"],
  },
  {
    name: "Contract",
    label: "Contract Type",
    type: "select",
    options: ["Month-to-month", "One year", "Two year"],
  },
  { name: "PaperlessBilling", label: "Paperless Billing", type: "yesNo" },
  {
    name: "PaymentMethod",
    label: "Payment Method",
    type: "select",
    options: [
      "Electronic check",
      "Mailed check",
      "Bank transfer (automatic)",
      "Credit card (automatic)",
    ],
  },
  {
    name: "MonthlyCharges",
    label: "Monthly Charges",
    type: "number",
    min: 0,
    step: "0.01",
  },
  {
    name: "TotalCharges",
    label: "Total Charges",
    type: "number",
    min: 0,
    step: "0.01",
    optional: true,
  },
];

const inputClass =
  "w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-white outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20";

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm text-slate-400">{label}</span>
      {children}
    </label>
  );
}

function getRiskAssessment(probability, customer, isIBM) {
  let level;
  let title;
  let description;
  let actions;

  if (probability < 25) {
    level = "Low";
    title = "Maintain customer satisfaction";
    description =
      "The estimated churn probability is relatively low. Continue providing reliable service and monitor customer engagement.";
    actions = [
      "Maintain consistent service quality.",
      "Continue routine customer engagement.",
      "Monitor future changes in customer behavior.",
    ];
  } else if (probability < 55) {
    level = "Medium";
    title = "Improve customer engagement";
    description =
      "The customer may benefit from a service review and proactive engagement before the risk increases.";
    actions = [
      "Review customer feedback and recent usage.",
      "Check for billing or service concerns.",
      "Share relevant plans or service benefits.",
    ];
  } else if (probability < 75) {
    level = "High";
    title = "Initiate proactive retention";
    description =
      "The model estimates elevated churn risk. Prioritize customer outreach and identify possible reasons for dissatisfaction.";
    actions = [
      "Contact the customer to understand their concerns.",
      "Review service quality and billing history.",
      "Offer a suitable plan or support option where appropriate.",
    ];
  } else {
    level = "Critical";
    title = "Prioritize retention outreach";
    description =
      "The estimated churn probability is very high. Prioritize a timely, personalized retention review.";
    actions = [
      "Prioritize direct customer outreach.",
      "Investigate contract, pricing, and support concerns.",
      "Consider a relevant retention offer based on customer needs.",
    ];
  }

  if (isIBM && customer) {
    const contextualActions = [];

    if (customer.Contract === "Month-to-month") {
      contextualActions.push(
        "Discuss whether a suitable longer-term plan would provide better value."
      );
    }

    if (customer.TechSupport === "No") {
      contextualActions.push(
        "Explain available technical support options."
      );
    }

    if (customer.OnlineSecurity === "No") {
      contextualActions.push(
        "Explain available online security options if relevant."
      );
    }

    if (
      customer.PaymentMethod === "Electronic check" &&
      probability >= 25
    ) {
      contextualActions.push(
        "Review billing preferences and explain available payment methods."
      );
    }

    actions = [...contextualActions, ...actions].slice(0, 5);
  }

  const colors = {
    Low: {
      border: "border-emerald-800/70",
      background: "bg-emerald-950/30",
      text: "text-emerald-300",
      badge: "bg-emerald-500/15",
    },
    Medium: {
      border: "border-yellow-800/70",
      background: "bg-yellow-950/30",
      text: "text-yellow-300",
      badge: "bg-yellow-500/15",
    },
    High: {
      border: "border-orange-800/70",
      background: "bg-orange-950/30",
      text: "text-orange-300",
      badge: "bg-orange-500/15",
    },
    Critical: {
      border: "border-red-800/70",
      background: "bg-red-950/30",
      text: "text-red-300",
      badge: "bg-red-500/15",
    },
  };

  return { level, title, description, actions, colors: colors[level] };
}

function ChurnPrediction() {
  const [modelMode, setModelMode] = useState("existing");
  const [form, setForm] = useState(initialForm);
  const [ibmForm, setIbmForm] = useState(initialIBMForm);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function handleIBMChange(event) {
    const { name, value, type } = event.target;

    setIbmForm((previous) => ({
      ...previous,
      [name]:
        type === "number"
          ? value === ""
            ? ""
            : Number(value)
          : name === "SeniorCitizen"
            ? Number(value)
            : value,
    }));
  }

  function switchModel(mode) {
    setModelMode(mode);
    setResult(null);
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    const payload = {
      ...form,
      age: Number(form.age),
      num_dependents: Number(form.num_dependents),
      estimated_salary: Number(form.estimated_salary),
      calls_made: Number(form.calls_made),
      sms_sent: Number(form.sms_sent),
      data_used: Number(form.data_used),
      tenure_months: Number(form.tenure_months),
      registration_year: Number(form.registration_year),
    };

    try {
      const data = await postAPI("/api/predict", payload);
      setResult({ ...data, modelMode: "existing" });
    } catch (err) {
      setError(err.message || "Unable to get a prediction.");
    } finally {
      setLoading(false);
    }
  }

  async function handleIBMSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    const payload = {
      ...ibmForm,
      SeniorCitizen: Number(ibmForm.SeniorCitizen),
      tenure: Number(ibmForm.tenure),
      MonthlyCharges: Number(ibmForm.MonthlyCharges),
      TotalCharges:
        ibmForm.TotalCharges === "" || ibmForm.TotalCharges == null
          ? null
          : Number(ibmForm.TotalCharges),
    };

    try {
      const data = await postIBMAPI(payload);
      setResult({ ...data, modelMode: "ibm" });
    } catch (err) {
      setError(err.message || "Unable to get an IBM prediction.");
    } finally {
      setLoading(false);
    }
  }

  function resetForm() {
    if (modelMode === "ibm") {
      setIbmForm(initialIBMForm);
    } else {
      setForm(initialForm);
    }

    setResult(null);
    setError("");
  }

  const isIBMResult = result?.modelMode === "ibm";

  const predictedChurn = result
    ? Number(isIBMResult ? result.predicted_churn : result.prediction)
    : null;

  const probability = result
    ? Number(result.churn_probability) * 100
    : 0;

  const hasProbability =
    Number.isFinite(probability) &&
    probability >= 0 &&
    probability <= 100;

  const riskAssessment = hasProbability
    ? getRiskAssessment(
        probability,
        isIBMResult ? ibmForm : null,
        isIBMResult
      )
    : null;

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-800 bg-gradient-to-br from-blue-950/70 to-slate-900 p-6 md:p-8">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-blue-500/15 p-3 text-blue-400">
            <BrainCircuit size={28} />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">
              Customer Churn Prediction
            </h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Analyze customer information to estimate churn probability
              and identify appropriate retention actions.
            </p>
          </div>
        </div>
      </section>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => switchModel("existing")}
          disabled={loading}
          className={`rounded-xl px-4 py-3 text-sm font-semibold transition ${
            modelMode === "existing"
              ? "bg-blue-600 text-white"
              : "border border-slate-700 text-slate-300 hover:bg-slate-800"
          }`}
        >
          Existing Telecom Model
        </button>

        <button
          type="button"
          onClick={() => switchModel("ibm")}
          disabled={loading}
          className={`rounded-xl px-4 py-3 text-sm font-semibold transition ${
            modelMode === "ibm"
              ? "bg-blue-600 text-white"
              : "border border-slate-700 text-slate-300 hover:bg-slate-800"
          }`}
        >
          IBM Telco Model (Experimental)
        </button>
      </div>

      {modelMode === "ibm" && (
        <div className="rounded-xl border border-amber-800/60 bg-amber-950/20 p-4 text-sm leading-6 text-amber-200">
          This experimental model was trained on the IBM Telco dataset.
          Its customer features differ from those used by the existing
          telecom model. Predictions are estimates, not guarantees.
        </div>
      )}

      <div className="grid items-start gap-6 xl:grid-cols-3">
        <form
          onSubmit={modelMode === "ibm" ? handleIBMSubmit : handleSubmit}
          className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900 p-5 md:p-6 xl:col-span-2"
        >
          <div className="flex items-center gap-2">
            <UserRound size={19} className="text-blue-400" />
            <h3 className="font-semibold text-white">
              {modelMode === "ibm"
                ? "IBM Telco Customer Information"
                : "Customer Information"}
            </h3>
          </div>

          {modelMode === "existing" ? (
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Telecom Partner">
                <select
                  name="telecom_partner"
                  value={form.telecom_partner}
                  onChange={handleChange}
                  className={inputClass}
                  required
                >
                  {["Airtel", "Reliance Jio", "Vodafone", "BSNL"].map(
                    (partner) => (
                      <option key={partner} value={partner}>
                        {partner}
                      </option>
                    )
                  )}
                </select>
              </Field>

              <Field label="Gender">
                <select
                  name="gender"
                  value={form.gender}
                  onChange={handleChange}
                  className={inputClass}
                  required
                >
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                </select>
              </Field>

              <Field label="State">
                <input
                  name="state"
                  value={form.state}
                  onChange={handleChange}
                  className={inputClass}
                  placeholder="Enter state"
                  required
                />
              </Field>

              <Field label="City">
                <input
                  name="city"
                  value={form.city}
                  onChange={handleChange}
                  className={inputClass}
                  placeholder="Enter city"
                  required
                />
              </Field>

              {fields.map((field) => (
                <Field key={field.name} label={field.label}>
                  <input
                    name={field.name}
                    type="number"
                    value={form[field.name]}
                    onChange={handleChange}
                    min={field.min}
                    max={field.max}
                    step="any"
                    className={inputClass}
                    required
                  />
                </Field>
              ))}
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2">
              {ibmFields.map((field) => (
                <Field key={field.name} label={field.label}>
                  {field.type === "number" ? (
                    <input
                      name={field.name}
                      type="number"
                      min={field.min}
                      max={field.max}
                      step={field.step || "1"}
                      value={ibmForm[field.name]}
                      onChange={handleIBMChange}
                      className={inputClass}
                      required={!field.optional}
                    />
                  ) : (
                    <select
                      name={field.name}
                      value={ibmForm[field.name]}
                      onChange={handleIBMChange}
                      className={inputClass}
                      required
                    >
                      {field.type === "yesNo" ? (
                        <>
                          <option value="Yes">Yes</option>
                          <option value="No">No</option>
                        </>
                      ) : (
                        field.options.map((option) => {
                          const isObject = typeof option === "object";
                          const value = isObject ? option.value : option;
                          const label = isObject ? option.label : option;

                          return (
                            <option key={String(value)} value={value}>
                              {label}
                            </option>
                          );
                        })
                      )}
                    </select>
                  )}
                </Field>
              ))}
            </div>
          )}

          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-300">
              <AlertCircle size={19} className="mt-0.5 shrink-0" />
              <div>
                <p className="font-semibold">Prediction failed</p>
                <p className="mt-1 break-words">{error}</p>
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-3 border-t border-slate-800 pt-5">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Activity size={17} />
              {loading ? "Analyzing..." : "Predict Churn"}
            </button>

            <button
              type="button"
              onClick={resetForm}
              disabled={loading}
              className="flex items-center gap-2 rounded-xl border border-slate-700 px-5 py-3 text-sm text-slate-300 transition hover:bg-slate-800 disabled:opacity-50"
            >
              <RotateCcw size={16} />
              Reset
            </button>
          </div>
        </form>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5 md:p-6">
          <div className="flex items-center gap-2">
            <BrainCircuit size={19} className="text-blue-400" />
            <h3 className="font-semibold text-white">Prediction Result</h3>
          </div>

          {!result ? (
            <div className="py-12 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-800 text-slate-500">
                <Activity size={28} />
              </div>
              <p className="mt-4 font-medium text-slate-300">
                No prediction yet
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                Complete the form and select Predict Churn to see the result.
              </p>
            </div>
          ) : (
            <div className="mt-6 space-y-5">
              <div
                className={`rounded-xl border p-4 ${
                  predictedChurn === 1
                    ? "border-amber-800/70 bg-amber-950/30"
                    : "border-emerald-800/70 bg-emerald-950/30"
                }`}
              >
                <p className="text-xs text-slate-400">Model classification</p>
                <p
                  className={`mt-2 text-xl font-bold ${
                    predictedChurn === 1
                      ? "text-amber-300"
                      : "text-emerald-300"
                  }`}
                >
                  {result.prediction_label ||
                    (predictedChurn === 1 ? "Churn" : "No Churn")}
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-slate-400">
                    Churn probability
                  </span>
                  <span className="text-xl font-bold text-white">
                    {hasProbability ? `${probability.toFixed(2)}%` : "N/A"}
                  </span>
                </div>

                <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-blue-500 transition-all"
                    style={{
                      width: `${
                        hasProbability
                          ? Math.min(100, Math.max(0, probability))
                          : 0
                      }%`,
                    }}
                  />
                </div>
              </div>

              {riskAssessment && (
                <div
                  className={`rounded-xl border p-4 ${riskAssessment.colors.border} ${riskAssessment.colors.background}`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h4 className="font-semibold text-white">
                      Customer Risk Assessment
                    </h4>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-bold ${riskAssessment.colors.badge} ${riskAssessment.colors.text}`}
                    >
                      {riskAssessment.level} Risk
                    </span>
                  </div>

                  <h5
                    className={`mt-4 font-semibold ${riskAssessment.colors.text}`}
                  >
                    {riskAssessment.title}
                  </h5>

                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    {riskAssessment.description}
                  </p>

                  <div className="mt-4 border-t border-slate-700 pt-4">
                    <div className="flex items-center gap-2">
                      <Lightbulb size={17} className="text-blue-400" />
                      <p className="text-sm font-semibold text-white">
                        Recommended retention actions
                      </p>
                    </div>

                    <ul className="mt-3 space-y-3">
                      {riskAssessment.actions.map((action, index) => (
                        <li
                          key={`${riskAssessment.level}-${index}`}
                          className="flex items-start gap-2 text-sm leading-5 text-slate-300"
                        >
                          <CheckCircle2
                            size={16}
                            className="mt-0.5 shrink-0 text-blue-400"
                          />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {isIBMResult && (
                <div className="rounded-xl border border-slate-700 bg-slate-950/60 p-3">
                  <p className="text-sm text-slate-300">
                    Decision threshold:{" "}
                    <span className="font-semibold text-white">
                      {Number.isFinite(Number(result.threshold))
                        ? `${(Number(result.threshold) * 100).toFixed(0)}%`
                        : "N/A"}
                    </span>
                  </p>
                  <p className="mt-2 text-xs leading-5 text-slate-400">
                    The model predicts churn when the estimated probability
                    meets or exceeds its decision threshold.
                  </p>
                </div>
              )}

              {isIBMResult ? (
                <div className="flex items-start gap-3 rounded-xl border border-amber-900/60 bg-amber-950/20 p-3">
                  <ShieldAlert
                    size={19}
                    className="mt-0.5 shrink-0 text-amber-400"
                  />
                  <div>
                    <p className="text-sm font-semibold text-amber-300">
                      Experimental model
                    </p>
                    <p className="mt-2 text-xs leading-5 text-amber-100/70">
                      {result.notice ||
                        "This prediction is an estimate and is not a guarantee of customer behavior."}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-3 rounded-xl border border-amber-900/60 bg-amber-950/20 p-3">
                  <ShieldAlert
                    size={19}
                    className="mt-0.5 shrink-0 text-amber-400"
                  />
                  <div>
                    <p className="text-sm font-semibold text-amber-300">
                      Model reliability
                      {result.model_reliability != null
                        ? `: ${result.model_reliability}`
                        : ""}
                    </p>
                    <p className="mt-2 text-xs leading-5 text-amber-100/70">
                      {result.note ||
                        "Predictions are estimates and should be reviewed alongside customer context."}
                    </p>
                  </div>
                </div>
              )}

              <p className="text-xs leading-5 text-slate-500">
                Model: {result.model || "Existing Telecom Model"}
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default ChurnPrediction;
