import { Component, OnInit } from '@angular/core';
import { ApiService, Transaction } from './api.service';
import { NgFor } from '@angular/common';

@Component({
  selector: 'app-transaction-list',
  standalone: true,
  imports: [NgFor],
  template: `
    <section class="card">
      <h2>Transaction Journal</h2>
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Account</th>
            <th>Type</th>
            <th>Amount</th>
            <th>Date</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let txn of transactions">
            <td>{{ txn.transaction_id }}</td>
            <td>{{ txn.account_id }}</td>
            <td>{{ txn.transaction_type }}</td>
            <td>{{ txn.amount }}</td>
            <td>{{ txn.date }}</td>
            <td>{{ txn.time }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  `,
})
export class TransactionListComponent implements OnInit {
  transactions: Transaction[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.listTransactions().subscribe((resp) => (this.transactions = resp.transactions));
  }
}
