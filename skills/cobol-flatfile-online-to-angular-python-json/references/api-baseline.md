# API Baseline and Extension Rules

## Baseline endpoints

Use these endpoints as the default foundation. Extend only when COBOL logic indicates additional actions.

- `GET /health`
- `GET /accounts`
- `POST /accounts`
- `GET /accounts/{id}`
- `POST /accounts/{id}/deposit`
- `POST /accounts/{id}/withdraw`
- `GET /accounts/{id}/statement`
- `POST /accounts/{id}/apply-interest`

## Extension rules

1. Add endpoints only if a COBOL menu option or paragraph describes a unique action.
2. Prefer `POST /resource/{id}/action` for mutating operations.
3. Prefer `GET /resource/{id}` for read-only details.
4. Mirror COBOL menu labels in UI routes, but keep REST paths concise.

## Defaults

- Money handled as Decimal.
- Default interest rate 1%.
- Statement limit 10.
