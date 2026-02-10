# Mainframe Demo: COBOL to Angular + Python (Codex Skill)

This repository demonstrates a COBOL mainframe migration to a modern web application using a Codex skill. The target architecture is a responsive Angular frontend backed by a Python (FastAPI) REST API with JSON file persistence.

The legacy application is stored under `_legacy` and can be run with gnucobol. To install gnucobol run:

```bash
brew install gnucobol
```

Then the legacy application (code and data) can be built and run with

```bash
cobc -x -free BANKACCT.cob
./BANKACCT
```

Create the initial data files with:

```bash
cp CUSTOMERS.DAT.original CUSTOMERS.DAT 
cp TRANSACTIONS.DAT.original TRANSACTIONS.DAT
```

The output from Codex has been stored in `output`. If you want to run the migration itself, install the skill, create a new repo without an `output` folder, connect it to Codex and run the below migration prompt. Theresult shall look similar to:

![ExampleScreen](example.png)

## Local Install of the Skill

The skill lives in this repo under `skills/` and must be copied into your Codex skills directory.

### 1) Locate the skill folder

By default, the skill path is:

```
~/work/mainframe-demo/skills/cobol-flatfile-online-to-angular-python-json
```

### 2) Copy the skill into Codex

Run the following commands:

```bash
mkdir -p ~/.codex/skills
cp -R ~/work/mainframe-demo/skills/cobol-flatfile-online-to-angular-python-json ~/.codex/skills/
```

### 3) Restart Codex

Restart Codex so it can pick up the newly installed skill.

## Notes

- This installation is local-only. If you move the repo or rename the skill folder, update the source path accordingly.
- The skill should appear in Codex after restart.

## CODEX Migration Prompt

How to use: Start a Codex run in this repo and paste the prompt below. The prompt is written to ensure COBOL behavior overrides skill defaults.

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
