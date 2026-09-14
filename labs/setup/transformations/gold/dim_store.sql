CREATE OR REPLACE TABLE gold.dim_store USING DELTA AS
SELECT
    store_key,
    store_name,
    store_type,
    city,
    neighborhood_or_channel,
    is_online,
    store_area_sqm,
    seating_capacity,
    num_employees,
    store_manager,
    tax_rate,
    country_name,
    country_iso2,
    country_iso3,
    state_province,
    state_iso2,
    county_district,
    postal_code,
    latitude,
    longitude
FROM silver.dim_store;
