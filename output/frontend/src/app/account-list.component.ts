import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ApiService, Account } from './api.service';
import { NgFor, NgIf } from '@angular/common';

@Component({
  selector: 'app-account-list',
  standalone: true,
  imports: [RouterLink, NgFor, NgIf],
  template: `
    <section class="card">
      <div style="display:flex; justify-content: space-between; align-items:center;">
        <h2>Account Snapshot</h2>
        <a routerLink="/accounts/new"><button>Create Account</button></a>
      </div>
      <table class="table" *ngIf="accounts.length; else empty">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Balance</th>
            <th>Type</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let acct of accounts">
            <td>{{ acct.account_id }}</td>
            <td>{{ acct.name }}</td>
            <td>{{ acct.balance }}</td>
            <td>{{ acct.account_type }}</td>
            <td><a [routerLink]="['/accounts', acct.account_id]">View</a></td>
          </tr>
        </tbody>
      </table>
      <ng-template #empty>
        <p>No accounts yet. Create one to begin.</p>
      </ng-template>
    </section>
  `,
})
export class AccountListComponent implements OnInit {
  accounts: Account[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.listAccounts().subscribe((resp) => (this.accounts = resp.accounts));
  }
}
