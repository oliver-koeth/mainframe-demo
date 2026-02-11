import { test, expect } from '@playwright/test';

const uniqueName = () => `Heartbeat ${Date.now()}`;

test('create scheduled task via wizard, run, view log, delete', async ({ page }) => {
  const taskName = uniqueName();

  await page.goto('/scheduled-tasks');

  await page.fill('input[formcontrolname="display_name"]', taskName);
  await page.fill('input[formcontrolname="function_name"]', 'heartbeat');
  await page.selectOption('select[name="wizardType"]', 'interval');
  await page.fill('input[name="wizardMinutes"]', '5');
  await page.click('button:has-text("Apply")');

  await page.click('button:has-text("Create Task")');
  await expect(page.getByText(taskName)).toBeVisible();

  await page.click(`button.link:has-text("${taskName}")`);
  await page.click('button:has-text("Run Now")');
  await expect(page.getByText('Hello Heartbeat')).toBeVisible();

  page.on('dialog', (dialog) => dialog.accept());
  await page.click(`tr:has-text("${taskName}") button:has-text("Delete")`);
  await expect(page.getByText(taskName)).toHaveCount(0);
});
