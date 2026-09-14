CREATE OR REPLACE TABLE gold.dim_date USING DELTA AS
SELECT
    date_key,
    date,
    year,
    month,
    day,
    calendar_week,
    day_of_week,
    day_name,
    is_weekend,
    season,
    is_us_public_holiday
FROM silver.dim_date;
