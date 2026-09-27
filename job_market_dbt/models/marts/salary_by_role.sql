-- salary_by_role.sql
-- Aggregates salary stats by job title and country, using only postings
-- that actually have salary data (many don't, especially in India).
-- All salaries converted to USD for fair comparison across countries.

with converted as (
    select
        job_title,
        country,
        case
            when country = 'in' then salary_min / 83.0
            when country = 'gb' then salary_min * 1.27
            else salary_min
        end as salary_min_usd,
        case
            when country = 'in' then salary_max / 83.0
            when country = 'gb' then salary_max * 1.27
            else salary_max
        end as salary_max_usd
    from {{ ref('stg_job_postings') }}
    where salary_min is not null
      and salary_max is not null
),

jobs as (
    select
        job_title,
        country,
        salary_min_usd as salary_min,
        salary_max_usd as salary_max,
        (salary_min_usd + salary_max_usd) / 2.0 as salary_avg
    from converted
)

select
    job_title,
    country,
    count(*)                    as postings_with_salary,
    round(avg(salary_avg), 2)   as avg_salary,
    round(min(salary_min), 2)   as min_salary,
    round(max(salary_max), 2)   as max_salary
from jobs
group by job_title, country
order by avg_salary desc