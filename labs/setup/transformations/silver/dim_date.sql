CREATE OR REPLACE TABLE silver.dim_date USING DELTA AS
SELECT
    *
FROM read_files(
  '/Volumes/${catalog}/bronze/raw/dim_date/',
  format => 'csv'
);
