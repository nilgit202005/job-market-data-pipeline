-- job_skills.sql
-- Produces one row per (job, skill) match by checking if a skill keyword
-- appears in the job description. Powers the "top skills" chart.

with skills_list (skill) as (
    values
        ('Python'), ('SQL'), ('Excel'), ('Power BI'), ('Tableau'),
        ('R'), ('Java'), ('AWS'), ('Azure'), ('GCP'),
        ('dbt'), ('Snowflake'), ('BigQuery'), ('Spark'), ('Hadoop'),
        ('Machine Learning'), ('Statistics'), ('ETL'), ('Airflow'),
        ('Looker'), ('SAS'), ('VBA'), ('Google Analytics'), ('Git')
),

jobs as (
    select
        adzuna_id,
        country,
        job_title,
        company_name,
        salary_min,
        salary_max,
        job_description
    from {{ ref('stg_job_postings') }}
)

select
    jobs.adzuna_id,
    jobs.country,
    jobs.job_title,
    jobs.company_name,
    jobs.salary_min,
    jobs.salary_max,
    skills_list.skill
from jobs
cross join skills_list
where jobs.job_description ~* ('\y' || skills_list.skill || '\y')