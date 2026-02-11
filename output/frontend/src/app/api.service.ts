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

export interface ScheduledTask {
  id: string;
  display_name: string;
  function_name: string;
  cron: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  last_run?: string | null;
}

export interface ScheduledTaskExecution {
  id: string;
  task_id: string;
  status: string;
  started_at: string;
  finished_at: string;
  log_path: string;
}

export interface ScheduledTaskLogItem {
  execution_id: string;
  log_path: string;
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

  listScheduledTasks(): Observable<{ tasks: ScheduledTask[] }> {
    return this.http.get<{ tasks: ScheduledTask[] }>(`${this.baseUrl}/scheduled-tasks`);
  }

  getScheduledTask(taskId: string): Observable<ScheduledTask> {
    return this.http.get<ScheduledTask>(`${this.baseUrl}/scheduled-tasks/${taskId}`);
  }

  createScheduledTask(payload: Omit<ScheduledTask, 'id' | 'created_at' | 'updated_at' | 'last_run'>): Observable<ScheduledTask> {
    return this.http.post<ScheduledTask>(`${this.baseUrl}/scheduled-tasks`, payload);
  }

  updateScheduledTask(
    taskId: string,
    payload: Omit<ScheduledTask, 'id' | 'created_at' | 'updated_at' | 'last_run'>
  ): Observable<ScheduledTask> {
    return this.http.put<ScheduledTask>(`${this.baseUrl}/scheduled-tasks/${taskId}`, payload);
  }

  deleteScheduledTask(taskId: string): Observable<{ status: string }> {
    return this.http.delete<{ status: string }>(`${this.baseUrl}/scheduled-tasks/${taskId}`);
  }

  listTaskExecutions(taskId: string): Observable<{ executions: ScheduledTaskExecution[] }> {
    return this.http.get<{ executions: ScheduledTaskExecution[] }>(
      `${this.baseUrl}/scheduled-tasks/${taskId}/executions`
    );
  }

  listTaskLogs(taskId: string): Observable<{ logs: ScheduledTaskLogItem[] }> {
    return this.http.get<{ logs: ScheduledTaskLogItem[] }>(`${this.baseUrl}/scheduled-tasks/${taskId}/logs`);
  }

  getTaskExecutionLog(taskId: string, executionId: string): Observable<string> {
    return this.http.get(`${this.baseUrl}/scheduled-tasks/${taskId}/executions/${executionId}/log`, {
      responseType: 'text',
    });
  }

  runScheduledTask(taskId: string): Observable<ScheduledTaskExecution> {
    return this.http.post<ScheduledTaskExecution>(`${this.baseUrl}/scheduled-tasks/${taskId}/run`, {});
  }
}
