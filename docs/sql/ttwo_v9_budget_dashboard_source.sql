-- DuckDB source extraction for the canonical TTWO V9 budget dashboard.
-- The Python builder projects the nested report into bounded dashboard datasets.
SELECT *
FROM read_json_auto(
    'reports/ttwo_v9_budget_report.json',
    format = 'auto',
    maximum_object_size = 33554432
);
