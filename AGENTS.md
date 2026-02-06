# Purpose

Provide a single, authoritative migration prompt and workflow expectations for converting BANKACCT.cob plus .DAT files into an Angular + FastAPI app using the COBOL migration skill. COBOL behavior overrides skill defaults.

# Prompt

```
CODEX Migration Prompt — COBOL BANKACCT to Angular + FastAPI

Use the skill: cobol-flatfile-online-to-angular-python-json.

Goal: Convert BANKACCT.cob plus CUSTOMERS.DAT and TRANSACTIONS.DAT into a runnable Angular (standalone components) + FastAPI app with JSON persistence and tests. COBOL is authoritative for behavior even when it conflicts with skill defaults.

Inputs and discovery
- Inventory BANKACCT.cob, CUSTOMERS.DAT, TRANSACTIONS.DAT.
- Fixed-width .DAT parsing, no delimiters. Field widths must match the FD layouts in BANKACCT.cob.
- Seed store.json from CUSTOMERS.DAT and TRANSACTIONS.DAT.

COBOL-first behavioral requirements (override skill defaults)
- Savings interest rate is 2% (not 1%).
- Mini statement limit is 5 (not 10).
- Interest applies only to account type S.
- Insufficient funds must block withdrawals; no negative balances.
- Duplicate account IDs overwrite existing records.
- Ignore unknown transaction types (e.g., X in sample data).
- Preserve transaction date/time format: YYYY/MM/DD and HH:MM:SS.

API requirements
- Start from references/api-baseline.md and extend to full CRUD for accounts.
- Transactions are append-only: create/log and read/query only. No update/delete.
- Explicit endpoints to include:
  - Accounts: GET /accounts, POST /accounts, GET /accounts/{id}, PUT /accounts/{id}, DELETE /accounts/{id}
  - Account actions: POST /accounts/{id}/deposit, POST /accounts/{id}/withdraw, POST /accounts/{id}/apply-interest, GET /accounts/{id}/statement
  - Transactions: POST /transactions (or POST /accounts/{id}/transactions), GET /transactions with filters, GET /transactions/{id}

UI requirements
- Modernized route names and layouts (do not mirror COBOL menu labels).
- Best-guess validations in UI: required account ID, non-empty name, positive amounts, account type in S/C.

Persistence
- Single store.json with atomic write (temp file + rename). Use a lock if needed.
- Money uses Decimal.

Testing
- pytest for backend domain/HTTP flows, including error/edge cases: missing account, insufficient funds, bad transaction type, duplicate overwrite.
- Playwright E2E for UI happy paths and edge cases.

Docs
- Emit mapping.md (COBOL paragraph -> REST endpoint -> UI route).
- Emit record-layouts.md with PIC clauses and inferred types.
- Emit unsupported-features.md only if unsupported features are detected.

Output layout
- Follow references/output-structure.md.
- Do not modify _legacy or skills in this repo.
```

# Run/Validate

- Backend: run unit/integration tests (e.g., `pytest`) as provided in the output structure.
- Frontend: run UI and E2E tests (e.g., `npm test`, `npx playwright test`) as provided in the output structure.
- Build: ensure the Angular app builds and the FastAPI app imports cleanly.
