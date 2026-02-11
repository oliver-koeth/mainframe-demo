# COBOL → REST → UI Mapping

| COBOL Paragraph | COBOL Purpose | REST Endpoint(s) | UI Route |
| --- | --- | --- | --- |
| `MAIN-PARA` | Menu loop / dispatcher | `GET /health` for status | `/dashboard` |
| `CREATE-ACCOUNT` | Add account record | `POST /accounts` | `/accounts/new` |
| `VIEW-ACCOUNTS` | List all accounts | `GET /accounts` | `/accounts` |
| `DEPOSIT-MONEY` | Add funds | `POST /accounts/{id}/deposit` | `/accounts/:id` |
| `WITHDRAW-MONEY` | Withdraw funds with balance check | `POST /accounts/{id}/withdraw` | `/accounts/:id` |
| `MINI-STATEMENT` | Show up to 5 transactions | `GET /accounts/{id}/statement` | `/accounts/:id` |
| `APPLY-INTEREST` | Apply 2% interest to savings | `POST /accounts/apply-interest` and `POST /accounts/{id}/apply-interest` | `/interest` and `/accounts/:id` |
| `LOG-TRANSACTION-*` | Append transaction record | `POST /transactions` (log), `GET /transactions` | `/transactions` |
| `GET-CURRENT-DATETIME` | Timestamp formatting | Implicit in transaction creation | n/a |

## File-to-Entity Mapping

| COBOL File | REST Resource | JSON Store Section | Notes |
| --- | --- | --- | --- |
| `CUSTOMERS.DAT` | `/accounts` | `accounts[]` | Fixed-width parsing; duplicate IDs overwrite existing records |
| `TRANSACTIONS.DAT` | `/transactions` | `transactions[]` | Unknown types ignored during seed import |

## Scheduled Tasks

| Feature | REST Endpoint(s) | UI Route |
| --- | --- | --- |
| Scheduled tasks management | `GET/POST/PUT/DELETE /scheduled-tasks` | `/scheduled-tasks` |
| Task executions | `GET /scheduled-tasks/{id}/executions` | `/scheduled-tasks` |
| Execution logs | `GET /scheduled-tasks/{id}/executions/{execution_id}/log` | `/scheduled-tasks` |
| Task log files | `GET /scheduled-tasks/{id}/logs` | `/scheduled-tasks` |
