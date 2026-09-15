CREATE OR REPLACE TABLE gold.dim_customer USING DELTA AS
SELECT
    customer_key,
    loyalty_segment,
    channel_preference,
    is_home_barista,
    city
FROM silver.dim_customer;
