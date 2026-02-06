# Record Layouts

## CUSTOMER-FILE (CUSTOMERS.DAT)

| Field | PIC | Width | Type | Notes |
| --- | --- | --- | --- | --- |
| `ACCT-ID` | `X(10)` | 10 | string | Account identifier |
| `NAME` | `X(30)` | 30 | string | Customer name |
| `BALANCE` | `9(7)V99` | 9 | decimal(9,2) | Implied 2 decimal places |
| `ACCT-TYPE` | `X(1)` | 1 | string | `S` or `C` |

## TRANSACTION-FILE (TRANSACTIONS.DAT)

| Field | PIC | Width | Type | Notes |
| --- | --- | --- | --- | --- |
| `TRANS-ACCT-ID` | `X(10)` | 10 | string | Account identifier |
| `TRANS-TYPE` | `X(1)` | 1 | string | `D`, `W`, or `I` (`X` ignored) |
| `TRANS-AMOUNT` | `9(7)V99` | 9 | decimal(9,2) | Implied 2 decimal places |
| `TRANS-DATE` | `X(10)` | 10 | string | `YYYY/MM/DD` |
| `TRANS-TIME` | `X(8)` | 8 | string | `HH:MM:SS` |
