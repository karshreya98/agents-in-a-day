CREATE OR REPLACE TABLE gold.dim_product USING DELTA AS
SELECT
    product_key,
    product_name,
    product_category,
    product_subcategory,
    is_beans,
    available_in_store,
    available_online,
    list_price_usd,
    cost_of_goods_usd
FROM silver.dim_product;
