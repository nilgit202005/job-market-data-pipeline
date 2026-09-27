"""
extract_remotive.py
Pulls remote job postings from the Remotive API (a second, independent
data source) and loads them into Postgres. Remotive's own rate-limit
guidance is a few requests a day, so this makes ONE call per search term
(no pagination) rather than looping pages.

Run: python extract_remotive.py
"""

import os
import json
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SEARCH_TERMS = ["data analyst", "business analyst", "data scientist"]

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
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.remotive_postings (
                id SERIAL PRIMARY KEY,
                remotive_id TEXT UNIQUE,
                search_term TEXT,
                fetched_at TIMESTAMP DEFAULT NOW(),
                raw_json JSONB
            );
        """)
    conn.commit()


def fetch_jobs(search_term):
    url = "https://remotive.com/api/remote-jobs"
    params = {"search": search_term, "limit": 100}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def insert_postings(conn, search_term, jobs):
    inserted = 0
    with conn.cursor() as cur:
        for job in jobs:
            remotive_id = str(job.get("id"))
            cur.execute(
                """
                INSERT INTO raw.remotive_postings (remotive_id, search_term, raw_json)
                VALUES (%s, %s, %s)
                ON CONFLICT (remotive_id) DO NOTHING;
                """,
                (remotive_id, search_term, json.dumps(job)),
            )
            inserted += cur.rowcount
    conn.commit()
    return inserted


def main():
    conn = get_connection()
    setup_schema(conn)

    total_inserted = 0
    for term in SEARCH_TERMS:
        print(f"\n=== Search: {term} ===")
        data = fetch_jobs(term)
        jobs = data.get("jobs", [])
        inserted = insert_postings(conn, term, jobs)
        total_inserted += inserted
        print(f"  -> {len(jobs)} fetched, {inserted} new rows inserted")

    conn.close()
    print(f"\nDone. Total new rows inserted: {total_inserted}")


if __name__ == "__main__":
    main()