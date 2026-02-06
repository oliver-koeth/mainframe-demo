import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ApiService, Account, Transaction } from './api.service';
import { NgIf, NgFor } from '@angular/common';

@Component({
  selector: 'app-account-detail',
  standalone: true,
  imports: [ReactiveFormsModule, NgIf, NgFor],
  template: `
    <section class="card" *ngIf="account">
      <h2>Account {{ account.account_id }}</h2>
      <p><strong>{{ account.name }}</strong> · {{ account.account_type }} · Balance {{ account.balance }}</p>
      <div class="grid">
        <form [formGroup]="depositForm" (ngSubmit)="deposit()">
          <label>Deposit</label>
          <input type="number" formControlName="amount" min="0" step="0.01" />
          <button type="submit" [disabled]="depositForm.invalid">Deposit</button>
        </form>
        <form [formGroup]="withdrawForm" (ngSubmit)="withdraw()">
          <label>Withdraw</label>
          <input type="number" formControlName="amount" min="0" step="0.01" />
          <button type="submit" [disabled]="withdrawForm.invalid">Withdraw</button>
        </form>
        <div>
          <label>Interest</label>
          <button class="secondary" (click)="applyInterest()">Apply 2% Interest</button>
        </div>
      </div>
    </section>

    <section class="card" *ngIf="transactions.length">
      <h3>Mini Statement (5 entries)</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Time</th>
            <th>Type</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let txn of transactions">
            <td>{{ txn.date }}</td>
            <td>{{ txn.time }}</td>
            <td>{{ txn.transaction_type }}</td>
            <td>{{ txn.amount }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <p *ngIf="error" style="color: #a33;">{{ error }}</p>
  `,
})
export class AccountDetailComponent implements OnInit {
  account?: Account;
  transactions: Transaction[] = [];
  error = '';

  depositForm = this.fb.group({
    amount: ['0.00', [Validators.required, Validators.min(0.01)]],
  });
  withdrawForm = this.fb.group({
    amount: ['0.00', [Validators.required, Validators.min(0.01)]],
  });

  constructor(private route: ActivatedRoute, private api: ApiService, private fb: FormBuilder) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.loadAccount(id);
  }

  private loadAccount(id: string): void {
    this.api.getAccount(id).subscribe({
      next: (acct) => {
        this.account = acct;
        this.loadStatement();
      },
      error: () => (this.error = 'Account not found'),
    });
  }

  private loadStatement(): void {
    if (!this.account) {
      return;
    }
    this.api.getStatement(this.account.account_id).subscribe({
      next: (resp) => (this.transactions = resp.transactions),
    });
  }

  deposit(): void {
    if (!this.account || this.depositForm.invalid) {
      return;
    }
    const amount = this.depositForm.value.amount ?? '0.00';
    this.api.deposit(this.account.account_id, String(amount)).subscribe({
      next: (resp) => {
        this.account = resp.account;
        this.loadStatement();
      },
      error: (err) => (this.error = err?.error?.detail ?? 'Deposit failed'),
    });
  }

  withdraw(): void {
    if (!this.account || this.withdrawForm.invalid) {
      return;
    }
    const amount = this.withdrawForm.value.amount ?? '0.00';
    this.api.withdraw(this.account.account_id, String(amount)).subscribe({
      next: (resp) => {
        this.account = resp.account;
        this.loadStatement();
      },
      error: (err) => (this.error = err?.error?.detail ?? 'Withdrawal failed'),
    });
  }

  applyInterest(): void {
    if (!this.account) {
      return;
    }
    this.api.applyInterest(this.account.account_id).subscribe({
      next: (resp) => {
        this.account = { ...this.account!, balance: resp.new_balance };
        this.loadStatement();
      },
      error: (err) => (this.error = err?.error?.detail ?? 'Interest could not be applied'),
    });
  }
}
