"""
extract.py
Pulls job postings from the Adzuna API across multiple countries and
search terms, loading the raw results into a Postgres 'raw' schema.

Run: python extract.py
"""

import os
import time
import json
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# --- Config: edit these to change what you pull ---
COUNTRIES = ["in", "gb", "us"]   # India, UK, US
SEARCH_TERMS = ["data analyst", "business analyst", "data scientist"]
RESULTS_PER_PAGE = 20
MAX_PAGES = 10                    # per country, per search term

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def setup_schema(conn):
    """Create the raw schema and table if they don't exist yet."""
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.job_postings (
                id SERIAL PRIMARY KEY,
                adzuna_id TEXT UNIQUE,
                search_term TEXT,
                country TEXT,
                fetched_at TIMESTAMP DEFAULT NOW(),
                raw_json JSONB
            );
        """)
    conn.commit()


def fetch_page(country, search_term, page_number):
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page_number}"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": search_term,
        "results_per_page": RESULTS_PER_PAGE,
        "content-type": "application/json",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def insert_postings(conn, country, search_term, postings):
    inserted = 0
    with conn.cursor() as cur:
        for job in postings:
            adzuna_id = job.get("id")
            cur.execute(
                """
                INSERT INTO raw.job_postings (adzuna_id, search_term, country, raw_json)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (adzuna_id) DO NOTHING;
                """,
                (adzuna_id, search_term, country, json.dumps(job)),
            )
            inserted += cur.rowcount
    conn.commit()
    return inserted


def main():
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise SystemExit("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY in .env")

    conn = get_connection()
    setup_schema(conn)

    total_inserted = 0

    for country in COUNTRIES:
        for search_term in SEARCH_TERMS:
            print(f"\n=== Country: {country} | Search: {search_term} ===")
            for page in range(1, MAX_PAGES + 1):
                print(f"Fetching page {page}...")
                data = fetch_page(country, search_term, page)
                postings = data.get("results", [])

                if not postings:
                    print("No more results, stopping this combo.")
                    break

                inserted = insert_postings(conn, country, search_term, postings)
                total_inserted += inserted
                print(f"  -> {len(postings)} fetched, {inserted} new rows inserted")

                time.sleep(1)  # be polite to the API

    conn.close()
    print(f"\nDone. Total new rows inserted: {total_inserted}")


if __name__ == "__main__":
    main()