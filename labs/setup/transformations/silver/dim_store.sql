CREATE OR REPLACE TABLE silver.dim_store USING DELTA AS
SELECT
    *
FROM read_files(
  '/Volumes/${catalog}/bronze/raw/dim_store/',
  format => 'csv'
);
