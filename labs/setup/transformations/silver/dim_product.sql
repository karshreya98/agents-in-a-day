CREATE OR REPLACE TABLE silver.dim_product USING DELTA AS
SELECT
    *
FROM read_files(
  '/Volumes/${catalog}/bronze/raw/dim_product/',
  format => 'csv'
);
