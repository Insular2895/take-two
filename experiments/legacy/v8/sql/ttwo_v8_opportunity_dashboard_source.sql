-- DuckDB source extraction for the canonical TTWO V8 opportunity dashboard.
-- The Python builder projects the nested report into bounded dashboard datasets.
SELECT *
FROM read_json_auto(
    'reports/ttwo_v8_opportunity_report.json',
    format = 'auto',
    maximum_object_size = 33554432
);
