---
name: cobol-flatfile-online-to-angular-python-json
description: Convert menu-driven COBOL "online" programs that read/write flat files (.cob + .dat/.cpy) into a runnable Angular frontend + FastAPI backend with JSON file persistence; use when modernizing COBOL interactive flows into REST + web UI with Playwright/pytest tests.
---

# Cobol Flatfile Online To Angular Python Json

## Overview

Translate a COBOL interactive/menu-driven program that uses sequential flat files into a modern web app: Angular (standalone components) + FastAPI + JSON file persistence with tests. Produce a full output repository plus a traceable mapping from COBOL paragraphs/files to UI routes and REST endpoints.

## Inputs & discovery

1. Inventory all `.cob`, `.dat`, and `.cpy` files in the workspace.
2. Extract file layouts (FD records) and identify keys, numeric fields, and implied decimals.
3. Extract paragraph flow and menu options (DISPLAY/ACCEPT, EVALUATE, PERFORM).
4. Detect unsupported features (CICS/IMS, VSAM/indexed, SQL, complex REDEFINES, dynamic CALLs) and plan to report them.

## Workflow (execute in order)

1. **Inventory COBOL and data files** and capture record layouts, file names, and record counts.
2. **Infer domain entities** (records → entities) and keys (account-id, customer-id, etc.).
3. **Infer actions/flows** from menu logic and paragraph calls.
4. **Define REST endpoints** and UI routes matching those flows. Start from the API baseline in `references/api-baseline.md` and extend only when COBOL logic adds actions.
5. **Generate backend** (FastAPI + Pydantic v2) with JSON persistence rules and atomic write.
6. **Generate frontend** (Angular standalone components + reactive forms) mirroring COBOL menus.
7. **Generate tests**: pytest for backend domain/HTTP flows, Playwright for end-to-end UI flows.
8. **Generate docs**: mapping table, record layouts, and unsupported-feature report (if any).

## Output expectations

Follow the default repository layout in `references/output-structure.md`. Ensure a runnable `backend/`, `frontend/`, and `docs/` tree with a `store.json` file for persistence.

## Persistence & defaults

1. Use a single JSON file `store.json` with versioned schema.
2. Apply atomic writes (write temp file + rename).
3. Use a simple lock file if concurrent writes are possible.
4. Handle money as Decimal; default interest rate 1%; statement limit 10.

## Testing requirements

1. Backend: pytest unit/integration tests that parse sample `.dat` files and validate key domain flows.
2. Frontend: Playwright E2E tests that mirror COBOL menu flows.
3. Ensure backend imports cleanly and Angular builds.

## Reporting

1. Always emit a **mapping document** (COBOL paragraph → REST endpoint → UI route).
2. Always emit **record layout documentation** with field names, PIC clauses, and inferred types.
3. If unsupported features are detected, emit a **blocked-features report** and stop or stub those flows.

## References

Use these reference files only when needed:

- `references/api-baseline.md` for the baseline REST endpoints and extension rules.
- `references/output-structure.md` for the expected repository tree and docs outputs.
