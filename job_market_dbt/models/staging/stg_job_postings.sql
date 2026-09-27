select
    adzuna_id,
    search_term,
    country,
    fetched_at,

    raw_json ->> 'title'                           as job_title,
    raw_json -> 'company' ->> 'display_name'        as company_name,
    raw_json -> 'category' ->> 'label'              as category,
    raw_json -> 'location' ->> 'display_name'       as location_name,

    (raw_json ->> 'created')::timestamp             as posted_at,
    (raw_json ->> 'latitude')::float                as latitude,
    (raw_json ->> 'longitude')::float                as longitude,

    (raw_json ->> 'salary_min')::numeric            as salary_min,
    (raw_json ->> 'salary_max')::numeric            as salary_max,
    (raw_json ->> 'salary_is_predicted')::int       as salary_is_predicted,

    raw_json ->> 'description'                      as job_description,
    raw_json ->> 'redirect_url'                      as job_url

from {{ source('raw', 'job_postings') }}