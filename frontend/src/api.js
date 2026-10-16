

const PYTHON_API_URL =
  import.meta.env.VITE_PYTHON_API_URL || "http://127.0.0.1:8003";

export const PYTHON_API_BASE = PYTHON_API_URL;

const SPRING_API_URL =
  import.meta.env.VITE_SPRING_API_URL || "http://localhost:8080";


// Python API: analytics and ML prediction
export async function fetchAPI(endpoint, options = {}) {
  const response = await fetch(`${PYTHON_API_URL}${endpoint}`, options);

  if (!response.ok) {
    let detail = `Python API error: ${response.status}`;
    try {
      const payload = await response.clone().json();
      if (payload?.detail) detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
    } catch { /* The response may not be JSON. */ }
    throw new Error(detail);
  }

  return response.json();
}

// Python API: POST requests, including churn prediction
export async function postAPI(endpoint, body) {
  const response = await fetch(`${PYTHON_API_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = `Python API error: ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
      }
    } catch {
      // Keep the HTTP status message if the response is not JSON.
    }
    throw new Error(detail);
  }

  return response.json();
}

// Spring Boot API: customer CRUD
export async function getCustomers() {
  const response = await fetch(`${SPRING_API_URL}/api/customers`);

  if (!response.ok) {
    throw new Error("Failed to fetch customers");
  }

  return response.json();
}

export async function getCustomersPage(page = 0, size = 10) {
  const response = await fetch(
    `${SPRING_API_URL}/api/customers/page?page=${page}&size=${size}`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch customer page");
  }

  return response.json();
}

export async function searchCustomersPage({
  search = "",
  churn = "",
  page = 0,
  size = 10,
} = {}) {
  const params = new URLSearchParams({
    page: String(page),
    size: String(size),
  });

  if (search.trim()) {
    params.set("search", search.trim());
  }

  if (churn !== "") {
    params.set("churn", String(churn));
  }

  const response = await fetch(
    `${SPRING_API_URL}/api/customers/search?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error("Failed to search customers");
  }

  return response.json();
}






export async function createCustomer(customer) {
  const response = await fetch(`${SPRING_API_URL}/api/customers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(customer),
  });

  if (!response.ok) {
    throw new Error("Failed to create customer");
  }

  return response.json();
}

export async function updateCustomer(id, customer) {
  const response = await fetch(`${SPRING_API_URL}/api/customers/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(customer),
  });

  if (!response.ok) {
    throw new Error("Failed to update customer");
  }

  return response.json();
}

export async function deleteCustomer(id) {
  const response = await fetch(`${SPRING_API_URL}/api/customers/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Failed to delete customer");
  }
}



const IBM_API_URL =
  import.meta.env.VITE_IBM_API_URL || "http://127.0.0.1:8003";

// Separate API for the experimental IBM Telco model
export async function postIBMAPI(body) {
  const response = await fetch(`${IBM_API_URL}/api/ibm-predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let message = `IBM prediction API error: ${response.status}`;

    try {
      const data = await response.json();
      if (data?.detail) {
        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      }
    } catch {
      // Keep the fallback message if the response is not JSON.
    }

    throw new Error(message);
  }

  return response.json();
}
