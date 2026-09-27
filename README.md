# Job Market Data Pipeline

An end-to-end data pipeline that pulls live job postings from two APIs, transforms them into clean, analysis-ready tables, and visualizes skills demand and salary trends across India, the UK, and the US.

## Architecture
Adzuna API + Remotive API → Python (extract) → PostgreSQL (Docker, raw schema) → dbt (transform) → Power BI (visualize)
- **Extraction**: Python scripts (`extract.py`, `extract_remotive.py`) pull job postings from the [Adzuna API](https://developer.adzuna.com/) (India, UK, US — data analyst, business analyst, data scientist roles) and the [Remotive API](https://remotive.com/api/remote-jobs) (remote tech jobs, includes built-in skill tags). Both scripts are idempotent — safe to re-run without creating duplicates.
- **Storage**: PostgreSQL running in Docker, raw JSON stored as-is in a `raw` schema.
- **Transformation**: dbt models in the `analytics` schema:
  - `stg_job_postings` / `stg_remotive_postings` — flatten raw JSON into clean columns
  - `job_skills` — extracts skill mentions from Adzuna descriptions via word-boundary regex matching
  - `salary_by_role` — aggregates salary by role and country, normalized to USD
  - `skills_by_source` — unions Adzuna's regex-matched skills with Remotive's own tags for cross-source comparison
- **Automation**: Windows Task Scheduler runs the extraction daily.
- **Visualization**: Power BI dashboard with DAX measures (`DISTINCTCOUNT`, `DIVIDE`, `RANKX`) — skills demand, salary by role, and a source comparison.

## Key findings

- Top requested skills: SQL, Python, Power BI, Excel, Machine Learning
- Highest-paying roles cluster in the US, $120K-$170K+ for senior/principal data roles
- ~70% of postings include salary data
- Remotive's remote-tech postings skew toward web/frontend skills vs. Adzuna's data-analyst-specific postings — a reminder that data source choice shapes what conclusions you can draw

## Running it locally

1. Get free API credentials from [Adzuna](https://developer.adzuna.com/) and add them to a `.env` file (see `.env.example`)
2. `docker compose up -d` — starts Postgres
3. `python -m venv venv && venv\Scripts\activate && pip install requests psycopg2-binary python-dotenv dbt-postgres`
4. `python extract.py` and `python extract_remotive.py` — pull the data
5. `cd job_market_dbt && dbt run` — build the models
6. Open the Power BI file and connect to `localhost:5432` / `job_market`

## Stack

Python · Docker · PostgreSQL · dbt · Power BI · Adzuna API · Remotive API

## Notable engineering details

- Caught and fixed a false-positive skill-matching bug (`ILIKE '%R%'` matching inside "for"/"your") using word-boundary regex
- Caught and fixed a currency-mismatch bug (comparing INR/GBP/USD salaries without conversion)
- Idempotent extraction (`ON CONFLICT DO NOTHING`) — safe for daily automated re-runs
