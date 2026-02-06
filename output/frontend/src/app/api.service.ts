import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Account {
  account_id: string;
  name: string;
  balance: string;
  account_type: string;
}

export interface Transaction {
  transaction_id: string;
  account_id: string;
  transaction_type: string;
  amount: string;
  date: string;
  time: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  health(): Observable<{ status: string }> {
    return this.http.get<{ status: string }>(`${this.baseUrl}/health`);
  }

  listAccounts(): Observable<{ accounts: Account[] }> {
    return this.http.get<{ accounts: Account[] }>(`${this.baseUrl}/accounts`);
  }

  getAccount(accountId: string): Observable<Account> {
    return this.http.get<Account>(`${this.baseUrl}/accounts/${accountId}`);
  }

  createAccount(payload: Account): Observable<Account> {
    return this.http.post<Account>(`${this.baseUrl}/accounts`, payload);
  }

  updateAccount(accountId: string, payload: Omit<Account, 'account_id'>): Observable<Account> {
    return this.http.put<Account>(`${this.baseUrl}/accounts/${accountId}`, payload);
  }

  deleteAccount(accountId: string): Observable<{ status: string }> {
    return this.http.delete<{ status: string }>(`${this.baseUrl}/accounts/${accountId}`);
  }

  deposit(accountId: string, amount: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/accounts/${accountId}/deposit`, { amount });
  }

  withdraw(accountId: string, amount: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/accounts/${accountId}/withdraw`, { amount });
  }

  applyInterest(accountId: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/accounts/${accountId}/apply-interest`, {});
  }

  applyInterestAll(): Observable<any> {
    return this.http.post(`${this.baseUrl}/accounts/apply-interest`, {});
  }

  getStatement(accountId: string): Observable<{ account_id: string; transactions: Transaction[] }> {
    return this.http.get<{ account_id: string; transactions: Transaction[] }>(
      `${this.baseUrl}/accounts/${accountId}/statement`
    );
  }

  listTransactions(): Observable<{ transactions: Transaction[] }> {
    return this.http.get<{ transactions: Transaction[] }>(`${this.baseUrl}/transactions`);
  }
}
