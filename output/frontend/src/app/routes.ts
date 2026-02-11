import { Routes } from '@angular/router';

import { DashboardComponent } from './dashboard.component';
import { AccountListComponent } from './account-list.component';
import { AccountFormComponent } from './account-form.component';
import { AccountDetailComponent } from './account-detail.component';
import { TransactionListComponent } from './transaction-list.component';
import { InterestComponent } from './interest.component';
import { ScheduledTasksComponent } from './scheduled-tasks.component';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'accounts', component: AccountListComponent },
  { path: 'accounts/new', component: AccountFormComponent },
  { path: 'accounts/:id', component: AccountDetailComponent },
  { path: 'transactions', component: TransactionListComponent },
  { path: 'interest', component: InterestComponent },
  { path: 'scheduled-tasks', component: ScheduledTasksComponent },
];
