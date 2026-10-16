
import { useState } from "react";

const SPRING_API_URL =
  import.meta.env.VITE_SPRING_API_URL || "http://localhost:8080";

const TEMPLATE_COLUMNS = [
  "customer_id",
  "telecom_partner",
  "gender",
  "age",
  "state",
  "city",
  "pincode",
  "date_of_registration",
  "num_dependents",
  "estimated_salary",
  "calls_made",
  "sms_sent",
  "data_used",
  "churn",
];

const TEMPLATE_ROW = [
  "CUST_EXAMPLE_001",
  "Airtel",
  "M",
  "28",
  "Karnataka",
  "Bangalore",
  "560001",
  "2023-01-15",
  "1",
  "55000",
  "40",
  "20",
  "2500",
  "0",
];

function downloadCsvTemplate() {
  const csvContent = [TEMPLATE_COLUMNS, TEMPLATE_ROW]
    .map((row) =>
      row
        .map((value) => `"${String(value).replace(/"/g, '""')}"`)
        .join(",")
    )
    .join("\r\n");

  const blob = new Blob(["\uFEFF", csvContent], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = "churniq_customer_template.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();

  // Delay cleanup to avoid interrupting the download in some browsers.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function CustomerCsvUpload({ onImportSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  function handleFileChange(event) {
    const selectedFile = event.target.files?.[0] || null;

    setFile(null);
    setResult(null);
    setError("");

    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Unsupported file type. Please select a .csv file.");
      event.target.value = "";
      return;
    }

    if (selectedFile.size === 0) {
      setError("The selected CSV file is empty.");
      event.target.value = "";
      return;
    }

    setFile(selectedFile);
  }

  async function handleUpload(event) {
    event.preventDefault();

    if (!file) {
      setError("Please select a valid CSV file.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${SPRING_API_URL}/api/customers/import`,
        {
          method: "POST",
          body: formData,
        }
      );

      const responseText = await response.text();
      let data = {};

      if (responseText) {
        try {
          data = JSON.parse(responseText);
        } catch {
          data = {};
        }
      }

      if (!response.ok) {
        throw new Error(
          data.message ||
            data.error ||
            `Import failed (HTTP ${response.status}). Please check your CSV and try again.`
        );
      }

      setResult(data);
      setFile(null);
      event.target.reset();

      if (Number(data.imported) > 0 && onImportSuccess) {
        await onImportSuccess();
      }
    } catch (err) {
      if (err instanceof TypeError) {
        setError(
          "Unable to connect to the Spring Boot backend. Check that it is running on port 8080."
        );
      } else {
        setError(err.message || "An unexpected error occurred during import.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-white">Import Customers</h2>

      <p className="mt-2 text-sm text-slate-300">
        Upload a CSV file to import customer records into ChurnIQ.
        Existing customer IDs will be skipped.
      </p>

      <button
        type="button"
        onClick={downloadCsvTemplate}
        className="mt-4 inline-flex items-center gap-2 rounded-lg border border-slate-600 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-blue-500 hover:bg-slate-800"
      >
        Download CSV Template
      </button>

      <p className="mt-2 text-xs text-slate-400">
        Use the template to match the expected column names and data format.
      </p>

      <form onSubmit={handleUpload} className="mt-5 space-y-4">
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={handleFileChange}
          disabled={loading}
          className="block w-full rounded-lg border border-slate-600 bg-slate-950 p-3 text-sm text-slate-200 file:mr-4 file:rounded-md file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:font-medium file:text-white hover:file:bg-blue-500 disabled:opacity-50"
        />

        {file && (
          <p className="text-sm text-slate-300">
            Selected: {file.name} (
            {(file.size / 1024).toFixed(1)} KB)
          </p>
        )}

        <button
          type="submit"
          disabled={loading || !file}
          className="rounded-lg bg-blue-600 px-5 py-2.5 font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Importing..." : "Upload CSV"}
        </button>
      </form>

      {error && (
        <p
          role="alert"
          className="mt-4 rounded-lg border border-rose-800 bg-rose-950/50 p-3 text-sm text-rose-300"
        >
          {error}
        </p>
      )}

      {result && (
        <div
          role="status"
          className="mt-5 rounded-lg border border-slate-700 bg-slate-950 p-4"
        >
          <h3 className="font-semibold text-white">Import Summary</h3>

          <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div>
              <p className="text-sm text-slate-400">Imported</p>
              <p className="text-2xl font-semibold text-emerald-400">
                {result.imported ?? 0}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-400">Skipped</p>
              <p className="text-2xl font-semibold text-amber-400">
                {result.skipped ?? 0}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-400">Errors</p>
              <p className="text-2xl font-semibold text-rose-400">
                {result.errors?.length ?? 0}
              </p>
            </div>
          </div>

          {result.errors?.length > 0 && (
            <details className="mt-5 rounded-lg border border-slate-700 bg-slate-900 p-3">
              <summary className="cursor-pointer text-sm font-semibold text-blue-400 hover:text-blue-300">
                View import details ({result.errors.length})
              </summary>

              <ul className="mt-3 max-h-60 list-disc space-y-2 overflow-y-auto pl-5 text-sm text-rose-300">
                {result.errors.slice(0, 100).map((item, index) => (
                  <li key={`${index}-${item}`}>{item}</li>
                ))}
              </ul>

              {result.errors.length > 100 && (
                <p className="mt-3 text-xs text-slate-400">
                  Showing the first 100 messages.
                </p>
              )}
            </details>
          )}

          {Number(result.imported) > 0 && (
            <p className="mt-4 text-sm text-emerald-400">
              Import completed. Newly imported customers were saved to MySQL.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
