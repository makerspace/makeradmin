# Running tests

## Only run specific tests

Add the `PYTEST_ADDOPTS` flag to filter what tests to run:

```bash
$ PYTEST_ADDOPTS='-k test_reminder_message_is_created_20_days_before_expiry_even_if_other_span_after' \
    make test
# test-test-1              | + wait_for_debugger_flags='-m debugpy --listen 0.0.0.0:5678 --wait-for-client'
```

## Start the tests with debugger

Add the environment variable `WAIT_FOR_DEBUGGER=1` to stop before the tests start, and wait for a debugger to attach:

```bash
WAIT_FOR_DEBUGGER=1 \
    make test
```

After a while, the terminal will print the following, below,

```bash
# test-test-1              | + python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m pytest --color=yes . --workers auto -ra
# test-test-1              | 0.00s - Debugger warning: It seems that frozen modules are being used, which may
# test-test-1              | 0.00s - make the debugger miss breakpoints. Please pass -Xfrozen_modules=off
# test-test-1              | 0.00s - to python to disable frozen modules.
# test-test-1              | 0.00s - Note: Debugging will proceed. Set PYDEVD_DISABLE_FILE_VALIDATION=1 to disable this validation.
```

then you can connect with a `debugpy` debugger using VS Code to `localhost:5678`.

You can use the prepared launch configuration called "Python Debugger: Attach to container".
