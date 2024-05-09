# How to add licenses

Add any number of html files to this folder with licenses. They will be combined into a single html file in the backend and presented to the user.

## Example content

```
📁 data
└── 📁 licenses
    ├── 📄 1-heading.html
    ├── 📄 2-draw-program.html
    ├── 📄 3-cad-program.html
    ├── 📄 ...
    ├── 📄 README.md
    └── 📄 .gitignore
```

The resulting licenses page will then contain the content of the files `1-heading.html`, `2-draw-program.html` and `3-cad-program.html` (and any other .html files that the folder contains) in the order of the file names.
