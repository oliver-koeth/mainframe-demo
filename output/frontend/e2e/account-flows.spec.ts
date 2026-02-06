import { test, expect } from '@playwright/test';

const uniqueId = () => `acct${Date.now()}`;

test('create account and log activity', async ({ page }) => {
  const accountId = uniqueId();

  await page.goto('/accounts/new');
  await page.fill('input[formcontrolname="account_id"]', accountId);
  await page.fill('input[formcontrolname="name"]', 'Playwright User');
  await page.fill('input[formcontrolname="balance"]', '100.00');
  await page.selectOption('select[formcontrolname="account_type"]', 'S');
  await page.click('button:has-text("Create Account")');

  await expect(page).toHaveURL(/\/accounts$/);
  await expect(page.getByText(accountId)).toBeVisible();

  await page.click(`a[href="/accounts/${accountId}"]`);
  await expect(page.getByText(`Account ${accountId}`)).toBeVisible();

  await page.fill('form:has-text("Deposit") input', '25.00');
  await page.click('form:has-text("Deposit") button');

  await page.fill('form:has-text("Withdraw") input', '10.00');
  await page.click('form:has-text("Withdraw") button');

  await expect(page.getByText('Mini Statement')).toBeVisible();
});
