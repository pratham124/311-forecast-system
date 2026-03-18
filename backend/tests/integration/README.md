# Integration Coverage

This suite maps directly to `docs/UC-01-AT.md`.

- `test_ingestion_success.py` covers AT-01.
- `test_ingestion_source_failures.py` covers AT-02 and AT-03.
- `test_ingestion_no_new_records.py` covers AT-04.
- `test_ingestion_processing_failures.py` covers AT-05 and AT-06.
- `test_no_partial_activation.py` covers AT-07.
- Failure-notification assertions in the failure integration tests cover AT-08.
