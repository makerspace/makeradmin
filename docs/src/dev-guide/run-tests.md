# Running tests

## Backend tests

### Only run specific tests

Add the `PYTEST_ADDOPTS` flag to filter what tests to run:

```bash
$ PYTEST_ADDOPTS='-k test_reminder_message_is_created_20_days_before_expiry_even_if_other_span_after' \
    make test
```

### Debug tests

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

then you can connect with a _debugpy_ debugger to `localhost:5678`.

#### VS code configuration

You can use the following VS code launch configuration to attach to the _debugpy_ session:

```json hl_lines="4-19"
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Attach to container",
            "type": "debugpy",
            "request": "attach",
            "connect": { "host": "localhost", "port": 5678 },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/api/",
                    "remoteRoot": "/work/"
                },
                {
                    "localRoot": "${workspaceFolder}/venv",
                    "remoteRoot": "/usr/local/lib/python3.11/site-packages"
                }
            ]
        }
    ]
}
```

## Frontend tests

### From the terminal

```bash
# In the admin-directory, run
npm test
```

You can also rerun tests on changes, by passing the `--watch` option to jest:

```bash
npm test -- --watch
```

### Interactively in VS code

Add the following launch configuration to the .vscode directory in the root of the project.

```json hl_lines="4-19"
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug admin Jest Tests",
            "type": "node",
            "request": "launch",
            "runtimeArgs": [
                "--inspect-brk",
                "${workspaceRoot}/admin/node_modules/.bin/jest",
                "--runInBand"
            ],
            "cwd": "${workspaceFolder}/admin",
            "console": "integratedTerminal",
            "internalConsoleOptions": "neverOpen",
            "env": {
                "NODE_ENV": "--require babel-register"
            }
        }
    ]
}
```

You can then set breakpoints in the test and step through them interactively. See VS code's documentation for more information: <https://code.visualstudio.com/docs/editor/debugging>
