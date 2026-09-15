CREATE OR REPLACE TABLE silver.dim_customer USING DELTA AS
SELECT
    *
FROM read_files(
  '/Volumes/${catalog}/bronze/raw/dim_customer/',
  format => 'csv'
);
