import { Component } from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from './api.service';

@Component({
  selector: 'app-account-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <section class="card">
      <h2>Open a New Account</h2>
      <form [formGroup]="form" (ngSubmit)="submit()" class="grid">
        <div>
          <label>Account ID</label>
          <input formControlName="account_id" />
        </div>
        <div>
          <label>Name</label>
          <input formControlName="name" />
        </div>
        <div>
          <label>Initial Balance</label>
          <input type="number" formControlName="balance" min="0" step="0.01" />
        </div>
        <div>
          <label>Account Type</label>
          <select formControlName="account_type">
            <option value="">Select</option>
            <option value="S">Savings</option>
            <option value="C">Checking</option>
          </select>
        </div>
        <div style="grid-column: 1 / -1;">
          <button [disabled]="form.invalid">Create Account</button>
        </div>
      </form>
      <p *ngIf="error" style="color: #a33;">{{ error }}</p>
    </section>
  `,
})
export class AccountFormComponent {
  error = '';
  form = this.fb.group({
    account_id: ['', Validators.required],
    name: ['', Validators.required],
    balance: ['0.00', [Validators.required, Validators.min(0.01)]],
    account_type: ['', Validators.required],
  });

  constructor(private fb: FormBuilder, private api: ApiService, private router: Router) {}

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    const payload = {
      account_id: this.form.value.account_id ?? '',
      name: this.form.value.name ?? '',
      balance: this.form.value.balance ?? '0.00',
      account_type: this.form.value.account_type ?? '',
    };
    this.api.createAccount(payload).subscribe({
      next: () => this.router.navigate(['/accounts']),
      error: (err) => (this.error = err?.error?.detail ?? 'Unable to create account'),
    });
  }
}
