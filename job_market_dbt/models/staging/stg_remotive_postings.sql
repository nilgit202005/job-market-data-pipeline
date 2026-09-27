-- stg_remotive_postings.sql
-- Flattens raw Remotive JSON into clean columns.

select
    remotive_id,
    search_term,
    fetched_at,
    raw_json ->> 'title' as job_title,
    raw_json ->> 'company_name' as company_name,
    raw_json ->> 'category' as category,
    raw_json ->> 'candidate_required_location' as location_name,
    raw_json ->> 'salary' as salary_text,
    raw_json -> 'tags' as tags
from {{ source('raw', 'remotive_postings') }}