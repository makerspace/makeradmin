# Running tests

## Only run specific tests

Add the `PYTEST_ADDOPTS` flag to filter what tests to run:

```bash
$ PYTEST_ADDOPTS='-k test_reminder_message_is_created_20_days_before_expiry_even_if_other_span_after' \
    make test
```
