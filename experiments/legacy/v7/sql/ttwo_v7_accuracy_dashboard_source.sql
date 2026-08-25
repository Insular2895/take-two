-- DuckDB source extraction for the canonical TTWO V7 dashboard transformation.
-- The Python builder projects the nested report into bounded dashboard datasets.
SELECT *
FROM read_json_auto(
    'reports/ttwo_v7_accuracy_report.json',
    format = 'auto',
    maximum_object_size = 16777216
);
