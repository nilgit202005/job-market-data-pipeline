-- skills_by_source.sql
-- Unions skill mentions from BOTH data sources so they can be compared:
-- Adzuna (skill found via regex match in description) and Remotive
-- (skill/tag provided directly by the source, no matching needed).

with adzuna_skills as (
    select
        lower(trim(skill)) as skill,
        'adzuna' as source
    from {{ ref('job_skills') }}
),

remotive_tags as (
    select
        lower(trim(jsonb_array_elements_text(tags))) as skill,
        'remotive' as source
    from {{ ref('stg_remotive_postings') }}
    where tags is not null
)

select
    source,
    skill,
    count(*) as mentions
from (
    select * from adzuna_skills
    union all
    select * from remotive_tags
) combined
group by source, skill
order by source, mentions desc