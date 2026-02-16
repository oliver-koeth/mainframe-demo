import { Component, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators, FormsModule } from '@angular/forms';
import { NgFor, NgIf } from '@angular/common';
import { ApiService, ScheduledTask, ScheduledTaskExecution, ScheduledTaskLogItem } from './api.service';

const CRON_PATTERN = /^\S+\s+\S+\s+\S+\s+\S+\s+\S+$/;

@Component({
  selector: 'app-scheduled-tasks',
  standalone: true,
  imports: [ReactiveFormsModule, FormsModule, NgFor, NgIf],
  template: `
    <section class="card">
      <div class="toolbar">
        <div>
          <h2>Scheduled Tasks</h2>
          <p class="muted">Manage automated jobs and review recent executions.</p>
        </div>
        <button class="secondary" (click)="resetForm()">New Task</button>
      </div>
    </section>

    <section class="grid">
      <div class="card">
        <h3>Tasks</h3>
        <table class="table table-stack-actions tasks-table" *ngIf="tasks.length; else emptyState">
          <thead>
            <tr>
              <th>Name</th>
              <th>Enabled</th>
              <th>Cron</th>
              <th>Last Run</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let task of tasks">
              <td>
                <button class="link" (click)="selectTask(task)">{{ task.display_name }}</button>
                <div class="muted small">{{ task.function_name }}</div>
              </td>
              <td>
                <span class="tag" [class.on]="task.enabled">{{ task.enabled ? 'On' : 'Off' }}</span>
              </td>
              <td>{{ task.cron }}</td>
              <td>{{ task.last_run || '—' }}</td>
              <td class="row-actions">
                <div class="row-actions-inner">
                  <button class="secondary" (click)="editTask(task)">Edit</button>
                  <button class="danger" (click)="removeTask(task)">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <ng-template #emptyState>
          <p class="muted">No scheduled tasks yet.</p>
        </ng-template>
      </div>

      <div class="card">
        <h3>{{ editingTaskId ? 'Edit Task' : 'Create Task' }}</h3>
        <form [formGroup]="form" (ngSubmit)="submit()" class="stack">
          <div>
            <label>Display Name</label>
            <input formControlName="display_name" />
          </div>
          <div>
            <label>Function Name</label>
            <input formControlName="function_name" />
          </div>
          <div>
            <label>Cron (5 fields)</label>
            <input formControlName="cron" placeholder="*/5 * * * *" />
            <div class="error" *ngIf="form.controls.cron.invalid && form.controls.cron.touched">
              Enter a valid 5-field cron string.
            </div>
          </div>
          <div class="toggle">
            <label>Enabled</label>
            <input type="checkbox" formControlName="enabled" />
          </div>

          <div class="wizard">
            <h4>Cron Wizard</h4>
            <div class="grid">
              <div>
                <label>Minutes</label>
                <select [(ngModel)]="wizard.minute" [ngModelOptions]="{ standalone: true }" name="wizardMinute">
                  <option *ngFor="let option of minuteOptions" [value]="option">{{ option }}</option>
                </select>
              </div>
              <div>
                <label>Hours</label>
                <select [(ngModel)]="wizard.hour" [ngModelOptions]="{ standalone: true }" name="wizardHour">
                  <option *ngFor="let option of hourOptions" [value]="option">{{ option }}</option>
                </select>
              </div>
              <div>
                <label>Days</label>
                <select [(ngModel)]="wizard.day" [ngModelOptions]="{ standalone: true }" name="wizardDay">
                  <option *ngFor="let option of dayOptions" [value]="option">{{ option }}</option>
                </select>
              </div>
            </div>
            <button type="button" class="secondary" (click)="applyWizard()">Apply</button>
          </div>

          <div class="actions">
            <button [disabled]="form.invalid">{{ editingTaskId ? 'Save Changes' : 'Create Task' }}</button>
          </div>
        </form>
        <p class="error" *ngIf="error">{{ error }}</p>
      </div>

      <div class="card" *ngIf="selectedTask">
        <div class="toolbar">
          <div>
            <h3>Executions</h3>
            <p class="muted">{{ selectedTask.display_name }} · {{ selectedTask.cron }}</p>
          </div>
          <button (click)="runNow()">Run Now</button>
        </div>
        <table class="table table-stack-actions executions-table" *ngIf="executions.length; else noRuns">
          <thead>
            <tr>
              <th>Started</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let execution of executions">
              <td>{{ execution.started_at }}</td>
              <td>{{ execution.status }}</td>
              <td class="row-actions">
                <div class="row-actions-inner">
                  <button class="secondary" (click)="loadLog(execution)">View Log</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <ng-template #noRuns>
          <p class="muted">No executions yet.</p>
        </ng-template>

        <div class="log-list" *ngIf="logs.length">
          <h4>Log Files</h4>
          <ul class="plain-list">
            <li *ngFor="let log of logs">
              <button class="link" (click)="loadLogById(log.execution_id)">
                {{ log.execution_id }}.log
              </button>
            </li>
          </ul>
        </div>

        <div class="log" *ngIf="selectedLog">
          <h4>Execution Log</h4>
          <pre class="log-viewer">{{ selectedLog }}</pre>
        </div>
      </div>
    </section>
  `,
})
export class ScheduledTasksComponent implements OnInit {
  tasks: ScheduledTask[] = [];
  executions: ScheduledTaskExecution[] = [];
  logs: ScheduledTaskLogItem[] = [];
  selectedTask: ScheduledTask | null = null;
  selectedLog = '';
  editingTaskId: string | null = null;
  error = '';

  wizard = {
    minute: '*',
    hour: '*',
    day: '*',
  };

  minuteOptions = ['*', ...Array.from({ length: 60 }, (_, idx) => String(idx))];
  hourOptions = ['*', ...Array.from({ length: 24 }, (_, idx) => String(idx))];
  dayOptions = ['*', ...Array.from({ length: 31 }, (_, idx) => String(idx + 1))];

  form = this.fb.group({
    display_name: ['', Validators.required],
    function_name: ['', Validators.required],
    cron: ['', [Validators.required, Validators.pattern(CRON_PATTERN)]],
    enabled: [true],
  });

  constructor(private api: ApiService, private fb: FormBuilder) {}

  ngOnInit(): void {
    this.loadTasks();
  }

  loadTasks(): void {
    this.api.listScheduledTasks().subscribe({
      next: (resp) => {
        this.tasks = resp.tasks;
        if (this.selectedTask) {
          const updated = this.tasks.find((task) => task.id === this.selectedTask?.id) ?? null;
          this.selectedTask = updated;
        }
      },
      error: () => (this.error = 'Unable to load tasks'),
    });
  }

  resetForm(): void {
    this.editingTaskId = null;
    this.form.reset({
      display_name: '',
      function_name: '',
      cron: '',
      enabled: true,
    });
    this.error = '';
  }

  selectTask(task: ScheduledTask): void {
    this.selectedTask = task;
    this.selectedLog = '';
    this.loadExecutions(task.id);
    this.loadLogs(task.id);
  }

  editTask(task: ScheduledTask): void {
    this.editingTaskId = task.id;
    this.form.setValue({
      display_name: task.display_name,
      function_name: task.function_name,
      cron: task.cron,
      enabled: task.enabled,
    });
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const payload = {
      display_name: this.form.value.display_name ?? '',
      function_name: this.form.value.function_name ?? '',
      cron: this.form.value.cron ?? '',
      enabled: Boolean(this.form.value.enabled),
    };
    if (this.editingTaskId) {
      this.api.updateScheduledTask(this.editingTaskId, payload).subscribe({
        next: () => {
          this.loadTasks();
          this.resetForm();
        },
        error: (err) => (this.error = err?.error?.detail ?? 'Unable to update task'),
      });
      return;
    }
    this.api.createScheduledTask(payload).subscribe({
      next: () => {
        this.loadTasks();
        this.resetForm();
      },
      error: (err) => (this.error = err?.error?.detail ?? 'Unable to create task'),
    });
  }

  removeTask(task: ScheduledTask): void {
    if (!confirm(`Delete task ${task.display_name}?`)) {
      return;
    }
    this.api.deleteScheduledTask(task.id).subscribe({
      next: () => {
        if (this.selectedTask?.id === task.id) {
          this.selectedTask = null;
          this.executions = [];
          this.logs = [];
          this.selectedLog = '';
        }
        this.loadTasks();
      },
      error: () => (this.error = 'Unable to delete task'),
    });
  }

  loadExecutions(taskId: string): void {
    this.api.listTaskExecutions(taskId).subscribe({
      next: (resp) => (this.executions = resp.executions),
      error: () => (this.error = 'Unable to load executions'),
    });
  }

  loadLogs(taskId: string): void {
    this.api.listTaskLogs(taskId).subscribe({
      next: (resp) => (this.logs = resp.logs),
      error: () => (this.error = 'Unable to load log files'),
    });
  }

  loadLog(execution: ScheduledTaskExecution): void {
    if (!this.selectedTask) {
      return;
    }
    this.api.getTaskExecutionLog(this.selectedTask.id, execution.id).subscribe({
      next: (text) => (this.selectedLog = text),
      error: () => (this.selectedLog = 'Unable to load log.'),
    });
  }

  loadLogById(executionId: string): void {
    if (!this.selectedTask) {
      return;
    }
    this.api.getTaskExecutionLog(this.selectedTask.id, executionId).subscribe({
      next: (text) => (this.selectedLog = text),
      error: () => (this.selectedLog = 'Unable to load log.'),
    });
  }

  runNow(): void {
    if (!this.selectedTask) {
      return;
    }
    this.api.runScheduledTask(this.selectedTask.id).subscribe({
      next: (execution) => {
        this.loadExecutions(this.selectedTask!.id);
        this.loadLogs(this.selectedTask!.id);
        this.loadLog(execution);
      },
      error: () => (this.error = 'Unable to run task'),
    });
  }

  applyWizard(): void {
    const cron = `${this.wizard.minute} ${this.wizard.hour} ${this.wizard.day} * *`;
    this.form.patchValue({ cron });
  }
}
