import { Component } from '@angular/core';
import { ApiService } from './api.service';
import { NgIf, NgFor } from '@angular/common';

@Component({
  selector: 'app-interest',
  standalone: true,
  imports: [NgIf, NgFor],
  template: `
    <section class="card">
      <h2>Apply Savings Interest</h2>
      <p>Apply the 2% savings interest rate across all savings accounts.</p>
      <button (click)="apply()">Run Interest Batch</button>
      <div *ngIf="result">
        <p>Applied to {{ result.applied_count }} accounts.</p>
        <table class="table">
          <thead>
            <tr>
              <th>Account</th>
              <th>Interest</th>
              <th>New Balance</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let item of result.results">
              <td>{{ item.account_id }}</td>
              <td>{{ item.interest_amount }}</td>
              <td>{{ item.new_balance }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  `,
})
export class InterestComponent {
  result: any;

  constructor(private api: ApiService) {}

  apply(): void {
    this.api.applyInterestAll().subscribe((resp) => (this.result = resp));
  }
}
