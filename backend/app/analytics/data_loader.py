
import os
import time
from threading import Lock

import pandas as pd
import requests


SPRING_API_URL = os.getenv(
    "SPRING_API_URL",
    "http://localhost:8080",
).rstrip("/")

# Larger pages reduce the number of HTTP requests needed for large datasets.
PAGE_SIZE = 5000
REQUEST_TIMEOUT = 15
CACHE_TTL_SECONDS = 300

_cached_df = None
_cache_time = 0.0

# Protect cache reads and writes.
_cache_lock = Lock()

# Allow only one full-dataset refresh at a time.
# Normal cache reads remain available while a refresh is running.
_refresh_lock = Lock()


COLUMN_MAPPING = {
    "customerId": "customer_id",
    "telecomPartner": "telecom_partner",
    "dateOfRegistration": "date_of_registration",
    "numDependents": "num_dependents",
    "estimatedSalary": "estimated_salary",
    "callsMade": "calls_made",
    "smsSent": "sms_sent",
    "dataUsed": "data_used",
    "tenureMonths": "tenure_months",
    "registrationYear": "registration_year",
}


def _get_cached_data():
    """Return a copy of the cache and its age, if available."""
    with _cache_lock:
        if _cached_df is None:
            return None, 0.0

        return _cached_df.copy(), time.monotonic() - _cache_time


def _fetch_customer_data() -> pd.DataFrame:
    """Fetch and normalize all customer records from Spring Boot."""
    customers = []
    page = 0
    total_pages = None

    with requests.Session() as session:
        while total_pages is None or page < total_pages:
            response = session.get(
                f"{SPRING_API_URL}/api/customers/page",
                params={
                    "page": page,
                    "size": PAGE_SIZE,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            result = response.json()

            if not isinstance(result, dict):
                raise ValueError(
                    "Unexpected customer API response."
                )

            batch = result.get("content")

            if not isinstance(batch, list):
                raise ValueError(
                    "Customer API response is missing its content list."
                )

            customers.extend(batch)
            total_pages = int(result.get("totalPages", 0))

            if total_pages <= 0:
                break

            page += 1

    df = pd.DataFrame(customers)
    df = df.rename(columns=COLUMN_MAPPING)

    if not df.empty and "churn" in df.columns:
        df["churn"] = pd.to_numeric(
            df["churn"],
            errors="coerce",
        )

    if not df.empty and "date_of_registration" in df.columns:
        df["date_of_registration"] = pd.to_datetime(
            df["date_of_registration"],
            errors="coerce",
        )

    return df


def load_customer_data(force_refresh=False) -> pd.DataFrame:
    """
    Load customer records from Spring Boot/MySQL.

    - Reuse cached data for five minutes.
    - Fetch a fresh dataset when the cache expires.
    - Allow cached reads while a refresh is running.
    - Return stale cached data if Spring Boot has a temporary
      connection failure during refresh.
    - Return a copy so callers cannot modify the shared cache.

    Set force_refresh=True to request a fresh dataset.
    """
    global _cached_df, _cache_time

    cached_df, cache_age = _get_cached_data()

    if (
        not force_refresh
        and cached_df is not None
        and cache_age < CACHE_TTL_SECONDS
    ):
        return cached_df

    # Serialize full refreshes without blocking ordinary cache reads.
    with _refresh_lock:
        # Another request may have refreshed the cache while we waited.
        cached_df, cache_age = _get_cached_data()

        if (
            not force_refresh
            and cached_df is not None
            and cache_age < CACHE_TTL_SECONDS
        ):
            return cached_df

        try:
            df = _fetch_customer_data()
        except requests.RequestException:
            # Keep analytics available if the service temporarily fails.
            if cached_df is not None:
                return cached_df

            raise

        # Publish the complete dataset only after a successful fetch.
        with _cache_lock:
            _cached_df = df.copy()
            _cache_time = time.monotonic()

        return df.copy()


def invalidate_customer_cache():
    """
    Clear cached customer data after a successful customer creation,
    update, deletion, or CSV import.
    """
    global _cached_df, _cache_time

    with _cache_lock:
        _cached_df = None
        _cache_time = 0.0
