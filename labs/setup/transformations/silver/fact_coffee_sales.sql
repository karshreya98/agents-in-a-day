CREATE OR REPLACE TABLE silver.fact_coffee_sales USING DELTA
AS
SELECT
    *
FROM read_files(
  '/Volumes/${catalog}/bronze/raw/fact_coffee_sales/',
  format => 'parquet'
);
