import { useCallback, useEffect, useState } from "react";

import {

  Search, Users, ChevronLeft, ChevronRight, AlertCircle, RefreshCw,

  Plus, Pencil, Trash2, X, Save,

} from "lucide-react";

import CustomerCsvUpload from "./CustomerCsvUpload";

import {

  fetchAPI, searchCustomersPage, createCustomer, updateCustomer, deleteCustomer,

} from "../api";

const PAGE_SIZE = 10;

const EMPTY_FORM = {

  customerId: "",

  telecomPartner: "Airtel",

  gender: "M",

  age: 25,

  state: "",

  city: "",

  numDependents: 0,

  estimatedSalary: 0,

  callsMade: 0,

  smsSent: 0,

  dataUsed: 0,

  tenureMonths: 0,

  registrationYear: 2022,

  churn: 0,

};

const inputClass =

  "w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500";

function CustomerForm({ initialValue, onCancel, onSave, saving }) {

  const [form, setForm] = useState(() => ({

    ...EMPTY_FORM,

    ...(initialValue ?? {}),

  }));

  function changeField(event) {

    const { name, value } = event.target;

    const numericFields = [

      "age", "numDependents", "estimatedSalary", "callsMade", "smsSent",

      "dataUsed", "tenureMonths", "registrationYear", "churn",

    ];

    setForm((current) => ({

      ...current,

      [name]: numericFields.includes(name) ? Number(value) : value,

    }));

  }

  function submit(event) {

    event.preventDefault();

    onSave({

      ...form,

      customerId: form.customerId.trim(),

      state: form.state.trim(),

      city: form.city.trim(),

      churn: Number(form.churn),

    });

  }

  return (

    <form onSubmit={submit} className="space-y-5">

      <div className="grid gap-4 sm:grid-cols-2">

        <label className="space-y-1.5 text-sm text-slate-300">

          Customer ID \*

          <input className={inputClass} name="customerId" value={form.customerId ?? ""} onChange={changeField} required maxLength={100} placeholder="e.g. CUST001" />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          Telecom partner \*

          <select className={inputClass} name="telecomPartner" value={form.telecomPartner ?? "Airtel"} onChange={changeField} required>

            {["Airtel", "Jio", "Vi", "BSNL"].map((partner) => <option key={partner} value={partner}>{partner}</option>)}

          </select>

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          Gender

          <select className={inputClass} name="gender" value={form.gender ?? "M"} onChange={changeField}>

            <option value="M">Male</option><option value="F">Female</option><option value="Other">Other</option>

          </select>

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          Age

          <input className={inputClass} type="number" name="age" min="0" max="120" value={form.age ?? 25} onChange={changeField} required />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          State \*

          <input className={inputClass} name="state" value={form.state ?? ""} onChange={changeField} required />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          City \*

          <input className={inputClass} name="city" value={form.city ?? ""} onChange={changeField} required />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          Dependents

          <input className={inputClass} type="number" name="numDependents" min="0" value={form.numDependents ?? 0} onChange={changeField} />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          Estimated salary

          <input className={inputClass} type="number" name="estimatedSalary" min="0" step="0.01" value={form.estimatedSalary ?? 0} onChange={changeField} />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          Calls made

          <input className={inputClass} type="number" name="callsMade" min="0" value={form.callsMade ?? 0} onChange={changeField} />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          SMS sent

          <input className={inputClass} type="number" name="smsSent" min="0" value={form.smsSent ?? 0} onChange={changeField} />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          Data used

          <input className={inputClass} type="number" name="dataUsed" min="0" step="0.01" value={form.dataUsed ?? 0} onChange={changeField} />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          Tenure (months)

          <input className={inputClass} type="number" name="tenureMonths" min="0" value={form.tenureMonths ?? 0} onChange={changeField} />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300">

          Registration year

          <input className={inputClass} type="number" name="registrationYear" min="1900" max="2100" value={form.registrationYear ?? 2022} onChange={changeField} />

        </label>

        <label className="space-y-1.5 text-sm text-slate-300 sm:col-span-2">

          Churn status

          <select className={inputClass} name="churn" value={form.churn ?? 0} onChange={changeField}>

            <option value={0}>Retained</option><option value={1}>Churned</option>

          </select>

        </label>

      </div>

      <div className="flex justify-end gap-3 border-t border-slate-800 pt-4">

        <button type="button" onClick={onCancel} className="rounded-xl border border-slate-700 px-4 py-2.5 text-sm text-slate-300 transition hover:bg-slate-800">Cancel</button>

        <button type="submit" disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50">

          <Save size={16} />{saving ? "Saving..." : "Save customer"}

        </button>

      </div>

    </form>

  );

}

export default function Customers() {

  const [customers, setCustomers] = useState([]);

  const [search, setSearch] = useState("");

  const [churn, setChurn] = useState("all");

  const [page, setPage] = useState(1);

  const [serverTotal, setServerTotal] = useState(0);

  const [serverTotalPages, setServerTotalPages] = useState(1);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [retryCount, setRetryCount] = useState(0);

  const [modalMode, setModalMode] = useState(null);

  const [selectedCustomer, setSelectedCustomer] = useState(null);

  const [saving, setSaving] = useState(false);

  const [actionError, setActionError] = useState("");

  const [notice, setNotice] = useState("");

  const loadCustomers = useCallback(async function loadCustomers() {

    setLoading(true);

    setError("");

    try {

      // The UI uses 1-based page numbers; Spring Data uses 0-based indexes.

      const data = await searchCustomersPage({

        search,

        churn: churn === "all" ? "" : churn,

        page: page - 1,

        size: PAGE_SIZE,

      });

      if (!data || !Array.isArray(data.content)) {

        throw new Error("Unexpected Spring Boot response: expected a paginated customer response.");

      }

      setCustomers(data.content);

      setServerTotal(Number(data.totalElements ?? 0));

      setServerTotalPages(Math.max(1, Number(data.totalPages ?? 1)));

    } catch (err) {

      setError(err.message || "Unable to load customers.");

    } finally {

      setLoading(false);

    }

  }, [page, search, churn]);

  useEffect(() => {
    // Initial and query-driven asynchronous page load.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadCustomers();
  }, [loadCustomers, retryCount]);

  const total = serverTotal;

  const totalPages = serverTotalPages;

  const currentPage = Math.min(page, totalPages);

  const visibleCustomers = customers;


  async function handleSave(customer) {
  setSaving(true);
  setActionError("");
  setNotice("");

  try {
    // Save the customer in Spring Boot / MySQL.
    if (modalMode === "edit" && selectedCustomer) {
      await updateCustomer(selectedCustomer.id, customer);
    } else {
      await createCustomer(customer);
    }

    // The customer has been saved successfully.
    setModalMode(null);
    setSelectedCustomer(null);

    // Invalidate cached analytics in the Python API.
    let cacheWarning = "";

    try {
      await fetchAPI("/internal/cache/invalidate", {
        method: "POST",
      });
    } catch (cacheError) {
      console.error(
        "Customer saved, but analytics cache invalidation failed:",
        cacheError
      );

      cacheWarning =
        " Analytics cache could not be refreshed automatically.";
    }

    setNotice(
      `${modalMode === "edit" ? "Customer updated" : "Customer created"} successfully.` +
        cacheWarning
    );

    // Reload the customer directory.
    await loadCustomers();
  } catch (err) {
    setActionError(err.message || "Unable to save customer.");
  } finally {
    setSaving(false);
  }
}
  async function handleDelete(customer) {

    if (!window.confirm(`Delete customer ${customer.customerId || customer.id}? This cannot be undone.`)) return;

    setActionError("");

    setNotice("");

    try {

      await deleteCustomer(customer.id);

      setNotice("Customer deleted successfully.");

      await loadCustomers();

    } catch (err) {

      setActionError(err.message || "Unable to delete customer.");

    }

  }

  function openCreateModal() {

    setSelectedCustomer(null);

    setActionError("");

    setModalMode("create");

  }

  function openEditModal(customer) {

    setSelectedCustomer(customer);

    setActionError("");

    setModalMode("edit");

  }

  return (

    <section className="space-y-6 text-slate-100">

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">

        <div>

          <p className="text-sm font-medium text-blue-400">WORKSPACE / CUSTOMERS</p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">Customer Directory</h1>

          <p className="mt-2 text-sm text-slate-400">Manage customer records stored in your Aveniq MySQL database.</p>

        </div>

        <button onClick={openCreateModal} className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500">

          <Plus size={17} />Add customer

        </button>

      </div>

      {notice && <div role="status" className="rounded-xl border border-emerald-800 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">{notice}</div>}

      {actionError && !modalMode && <div role="alert" className="rounded-xl border border-rose-800 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{actionError}</div>}

      <div className="grid gap-4 sm:grid-cols-2">

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">

          <div className="flex items-center justify-between"><p className="text-sm text-slate-400">Matching Customers</p><Users size={20} className="text-blue-400" /></div>

          <p className="mt-3 text-3xl font-bold text-white">{total.toLocaleString("en-IN")}</p>

          <p className="mt-2 text-xs text-slate-500">Total records in MySQL</p>

        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">

          <p className="text-sm text-slate-400">Current Page</p>

          <p className="mt-3 text-3xl font-bold text-white">{currentPage.toLocaleString("en-IN")}<span className="text-lg font-medium text-slate-500"> / {totalPages.toLocaleString("en-IN")}</span></p>

          <p className="mt-2 text-xs text-slate-500">Up to {PAGE_SIZE} records per page</p>

        </div>

      </div>

     <CustomerCsvUpload onImportSuccess={loadCustomers} />

      <div className="flex flex-col gap-3 sm:flex-row">

        <div className="relative min-w-0 flex-1">

          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />

          <input type="search" value={search} onChange={(event) => { setPage(1); setSearch(event.target.value); }} placeholder="Search all customers by ID, partner, city, or state..." aria-label="Search all customers" className="w-full rounded-xl border border-slate-700 bg-slate-900 py-3 pl-10 pr-4 text-sm text-white outline-none placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />

        </div>

        <select value={churn} onChange={(event) => { setPage(1); setChurn(event.target.value); }} aria-label="Filter customers by churn status" className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-blue-500">

          <option value="all">All Customers</option><option value="1">Churned</option><option value="0">Retained</option>

        </select>

      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">

        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 px-5 py-4">

          <h2 className="font-semibold text-white">Customer Records</h2>

          <span className="text-xs text-slate-500">{total.toLocaleString("en-IN")} total records</span>

        </div>

        {loading ? (

          <div className="p-10 text-center text-sm text-slate-400">Loading customers from MySQL...</div>

        ) : error ? (

          <div className="flex items-start gap-3 p-6">

            <AlertCircle size={20} className="shrink-0 text-rose-400" />

            <div>

              <p className="font-medium text-rose-400">Unable to load customers</p>

              <p className="mt-2 text-sm text-slate-400">{error}</p>

              <button onClick={() => setRetryCount((count) => count + 1)} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white transition hover:bg-blue-500"><RefreshCw size={15} />Try again</button>

            </div>

          </div>

        ) : (

          <div className="overflow-x-auto">

            <table className="w-full min-w-[1050px] text-left text-sm">

              <thead className="border-b border-slate-800 bg-slate-950/50 text-xs uppercase tracking-wide text-slate-400">

                <tr>

                  <th className="px-5 py-4 font-medium">Customer ID</th><th className="px-5 py-4 font-medium">Partner</th><th className="px-5 py-4 font-medium">Age</th><th className="px-5 py-4 font-medium">Location</th><th className="px-5 py-4 text-right font-medium">Calls</th><th className="px-5 py-4 text-right font-medium">Data Used</th><th className="px-5 py-4 font-medium">Status</th><th className="px-5 py-4 text-right font-medium">Actions</th>

                </tr>

              </thead>

              <tbody>

                {visibleCustomers.map((customer) => (

                  <tr key={customer.id} className="border-b border-slate-800/70 transition last:border-0 hover:bg-slate-800/40">

                    <td className="px-5 py-4 font-medium text-white">#{customer.customerId || "—"}</td>

                    <td className="px-5 py-4 text-slate-300">{customer.telecomPartner || "—"}</td>

                    <td className="px-5 py-4 text-slate-300">{customer.age ?? "—"}</td>

                    <td className="px-5 py-4 text-slate-300">{customer.city || "—"}, {customer.state || "—"}</td>

                    <td className="px-5 py-4 text-right text-slate-300">{customer.callsMade ?? "—"}</td>

                    <td className="px-5 py-4 text-right text-slate-300">{customer.dataUsed == null ? "—" : Number(customer.dataUsed).toLocaleString("en-IN")}</td>

                    <td className="px-5 py-4"><span className={Number(customer.churn) === 1 ? "inline-flex rounded-full bg-rose-500/10 px-3 py-1 text-xs font-medium text-rose-400" : "inline-flex rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400"}>{Number(customer.churn) === 1 ? "Churned" : "Retained"}</span></td>

                    <td className="px-5 py-4"><div className="flex justify-end gap-2">

                      <button onClick={() => openEditModal(customer)} aria-label={`Edit ${customer.customerId}`} title="Edit customer" className="rounded-lg border border-slate-700 p-2 text-slate-300 transition hover:border-blue-500 hover:text-blue-400"><Pencil size={15} /></button>

                      <button onClick={() => handleDelete(customer)} aria-label={`Delete ${customer.customerId}`} title="Delete customer" className="rounded-lg border border-slate-700 p-2 text-slate-300 transition hover:border-rose-500 hover:text-rose-400"><Trash2 size={15} /></button>

                    </div></td>

                  </tr>

                ))}

                {visibleCustomers.length === 0 && <tr><td colSpan={8} className="px-5 py-12 text-center text-slate-400">{customers.length === 0 ? "No customers have been added to the MySQL database yet." : "No customers on this page match these filters. Try another page or adjust your search."}</td></tr>}

              </tbody>

            </table>

          </div>

        )}

      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">

        <p className="text-sm text-slate-400">Showing page {currentPage.toLocaleString("en-IN")} of {totalPages.toLocaleString("en-IN")}</p>

        <div className="flex gap-2">

          <button disabled={currentPage <= 1 || loading} onClick={() => setPage((current) => Math.max(1, current - 1))} className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-2.5 text-sm text-slate-300 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"><ChevronLeft size={16} />Previous</button>

          <button disabled={currentPage >= totalPages || loading} onClick={() => setPage((current) => Math.min(totalPages, current + 1))} className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40">Next<ChevronRight size={16} /></button>

        </div>

      </div>

      {modalMode && (

        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/70 p-4">

          <div role="dialog" aria-modal="true" aria-labelledby="customer-modal-title" className="my-8 w-full max-w-3xl rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-2xl sm:p-7">

            <div className="mb-5 flex items-start justify-between gap-4">

              <div><h2 id="customer-modal-title" className="text-xl font-semibold text-white">{modalMode === "edit" ? "Edit customer" : "Add customer"}</h2><p className="mt-1 text-sm text-slate-400">{modalMode === "edit" ? "Update the customer record in MySQL." : "Create a new customer record in MySQL."}</p></div>

              <button onClick={() => { setModalMode(null); setActionError(""); }} aria-label="Close form" className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-800 hover:text-white"><X size={18} /></button>

            </div>

            {actionError && <div role="alert" className="mb-4 rounded-xl border border-rose-800 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{actionError}</div>}

            <CustomerForm key={`${modalMode}-${selectedCustomer?.id ?? "new"}`} initialValue={selectedCustomer} onCancel={() => { setModalMode(null); setActionError(""); }} onSave={handleSave} saving={saving} />

          </div>

        </div>

      )}

    </section>

  );

}
