import { Component, OnInit } from '@angular/core';
import { ApiService } from './api.service';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [NgIf],
  template: `
    <section class="card">
      <h2>Welcome back</h2>
      <p>System status: <strong>{{ status }}</strong></p>
      <p>Use the navigation to manage accounts, log transactions, and apply interest.</p>
    </section>
  `,
})
export class DashboardComponent implements OnInit {
  status = 'checking...';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.health().subscribe({
      next: (resp) => (this.status = resp.status),
      error: () => (this.status = 'offline'),
    });
  }
}
