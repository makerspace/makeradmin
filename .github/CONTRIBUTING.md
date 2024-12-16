# Contributing to Makeradmin

Thank you for considering to contribute to Makeradmin! Here are some guidelines and rules to make it easier to collaborate.

## Code

Code needs to follow the formatting rules set up in the repository.
You should always format your code before each commit.
This can be done with the command `make format`.
Python code if formatted with `ruff` and web-code is formatted with `prettier`.

It is recommended to set up the pre-commit hooks to check the formatting before pushing to Github. They can be installed by running `make init-pre-commit`.

Formatting is also checked automatically when opening a pull request.

### IDE settings

- **VS-code:** If you are using VS code, then you can install the [recommended extensions](/.vscode/extensions.json). Then most files will auto-format on save.

    **You should not modify these files.**

## Commits

Commits should follow the following rules, in short:

1.  Use imperative mood in the subject line (i.e. "Auto-**format** with black" rather than "Auto-**formatted** with black")
1.  Start the subject line with a capital letter
1.  Explain what/why in the body of the commit message rather than how
1.  Separate changes into several commits if they change multiple "behaviors". For example, formatting changes should be in separate commits from functional changes. And ditto if functional changes can be broken down.

Having nice commit messages helps when reading why changes were applied and can guide readers of the code.
