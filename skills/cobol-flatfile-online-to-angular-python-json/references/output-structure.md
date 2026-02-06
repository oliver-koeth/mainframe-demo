# Expected Output Structure

Produce a runnable repository with this minimum tree:

```
output/
  backend/
    app/
      __init__.py
      main.py
      models.py
      storage.py
      services.py
    tests/
      test_storage.py
      test_api.py
    store.json
    pyproject.toml
    README.md
  frontend/
    src/
      app/
        app.component.ts
        app.component.html
        routes.ts
    e2e/
      account-flows.spec.ts
    package.json
    playwright.config.ts
    README.md
  docs/
    mapping.md
    record-layouts.md
    unsupported-features.md (only if needed)
```

Notes:

- Add or rename files if COBOL flows require it, but keep `backend/`, `frontend/`, and `docs/`.
- `store.json` must be the single persistence file.
- `docs/mapping.md` must map COBOL paragraphs and files to UI routes and REST endpoints.
