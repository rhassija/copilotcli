/**
 * E2E tests for authentication workflow.
 * 
 * Tests complete user authentication journey using Playwright.
 */

import { test, expect } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:3000';
const API_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const TEST_TOKEN = process.env.TEST_GITHUB_TOKEN || 'ghp_test_token_for_e2e';

test.describe('Authentication E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage before each test
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      sessionStorage.clear();
      localStorage.clear();
    });
  });

  test('should display login page on initial visit', async ({ page }) => {
    await page.goto(BASE_URL);

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);

    // Verify login page elements
    await expect(page.getByText('Copilot CLI')).toBeVisible();
    await expect(page.getByText('Sign in with GitHub')).toBeVisible();
    await expect(page.getByLabel('GitHub Personal Access Token')).toBeVisible();
    await expect(page.getByRole('button', { name: /verify token/i })).toBeVisible();
  });

  test('should show validation error for empty token', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Click submit without entering token
    const submitButton = page.getByRole('button', { name: /verify token/i });
    await submitButton.click();

    // Should show error message
    await expect(page.getByText('Please enter a GitHub token')).toBeVisible();

    // Should not navigate away
    await expect(page).toHaveURL(/\/login/);
  });

  test('should paste token from clipboard', async ({ page, context }) => {
    await page.goto(`${BASE_URL}/login`);

    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Write token to clipboard
    await page.evaluate((token) => {
      return navigator.clipboard.writeText(token);
    }, TEST_TOKEN);

    // Click paste button
    const pasteButton = page.getByRole('button', { name: /paste/i });
    await pasteButton.click();

    // Verify token was pasted
    const tokenInput = page.getByLabel('GitHub Personal Access Token');
    await expect(tokenInput).toHaveValue(TEST_TOKEN);
  });

  test('should successfully login with valid token', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Enter token
    const tokenInput = page.getByLabel('GitHub Personal Access Token');
    await tokenInput.fill(TEST_TOKEN);

    // Submit form
    const submitButton = page.getByRole('button', { name: /verify token/i });
    await submitButton.click();

    // Should show loading state
    await expect(page.getByText('Verifying...')).toBeVisible();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Should display welcome message
    await expect(page.getByText(/Welcome back/i)).toBeVisible();
  });

  test('should show error for invalid token', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Enter invalid token
    const tokenInput = page.getByLabel('GitHub Personal Access Token');
    await tokenInput.fill('ghp_invalid_token_123');

    // Submit form
    const submitButton = page.getByRole('button', { name: /verify token/i });
    await submitButton.click();

    // Should show error message
    await expect(page.getByText(/Authentication failed/i)).toBeVisible({
      timeout: 10000,
    });

    // Should remain on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('should persist session across page refresh', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Login
    await page.getByLabel('GitHub Personal Access Token').fill(TEST_TOKEN);
    await page.getByRole('button', { name: /verify token/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Refresh page
    await page.reload();

    // Should still be on dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText(/Welcome back/i)).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel('GitHub Personal Access Token').fill(TEST_TOKEN);
    await page.getByRole('button', { name: /verify token/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Find and click logout button
    const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
    await logoutButton.click();

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);

    // Session should be cleared
    const sessionStorage = await page.evaluate(() =>
      window.sessionStorage.getItem('auth')
    );
    expect(sessionStorage).toBeNull();
  });

  test('should redirect to login when accessing protected route without auth', async ({
    page,
  }) => {
    // Try to access dashboard without authentication
    await page.goto(`${BASE_URL}/dashboard`);

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });

  test('should handle expired session gracefully', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel('GitHub Personal Access Token').fill(TEST_TOKEN);
    await page.getByRole('button', { name: /verify token/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Manually expire session (simulate backend session expiration)
    await page.evaluate(() => {
      const auth = JSON.parse(sessionStorage.getItem('auth') || '{}');
      auth.sessionId = 'expired_session_id';
      sessionStorage.setItem('auth', JSON.stringify(auth));
    });

    // Try to make API request (should detect expired session)
    await page.reload();

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test('should display user information after login', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Login
    await page.getByLabel('GitHub Personal Access Token').fill(TEST_TOKEN);
    await page.getByRole('button', { name: /verify token/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Should display user information in header/dashboard
    // Note: Actual assertions depend on your UI implementation
    await expect(page.getByText(/Welcome back/i)).toBeVisible();
  });

  test('should disable form during submission', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Enter token
    await page.getByLabel('GitHub Personal Access Token').fill(TEST_TOKEN);

    // Submit form
    const submitButton = page.getByRole('button', { name: /verify token/i });
    await submitButton.click();

    // Button should be disabled during submission
    await expect(submitButton).toBeDisabled();

    // Input should be disabled during submission
    const tokenInput = page.getByLabel('GitHub Personal Access Token');
    await expect(tokenInput).toBeDisabled();
  });

  test('should handle network errors gracefully', async ({ page, context }) => {
    // Block API requests to simulate network error
    await page.route(`${API_URL}/**`, (route) => route.abort('failed'));

    await page.goto(`${BASE_URL}/login`);

    // Try to login
    await page.getByLabel('GitHub Personal Access Token').fill(TEST_TOKEN);
    await page.getByRole('button', { name: /verify token/i }).click();

    // Should show error message
    await expect(page.getByText(/failed|error/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test('should clear error when user starts typing', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Submit empty form to trigger error
    await page.getByRole('button', { name: /verify token/i }).click();
    await expect(page.getByText('Please enter a GitHub token')).toBeVisible();

    // Start typing
    const tokenInput = page.getByLabel('GitHub Personal Access Token');
    await tokenInput.fill('ghp_');

    // Error should be cleared
    await expect(page.getByText('Please enter a GitHub token')).not.toBeVisible();
  });

  test('should maintain focus management for accessibility', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Token input should have autofocus
    const tokenInput = page.getByLabel('GitHub Personal Access Token');
    await expect(tokenInput).toBeFocused();

    // Tab to paste button
    await page.keyboard.press('Tab');
    const pasteButton = page.getByRole('button', { name: /paste/i });
    await expect(pasteButton).toBeFocused();

    // Tab to submit button
    await page.keyboard.press('Tab');
    const submitButton = page.getByRole('button', { name: /verify token/i });
    await expect(submitButton).toBeFocused();
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Enter token
    const tokenInput = page.getByLabel('GitHub Personal Access Token');
    await tokenInput.fill(TEST_TOKEN);

    // Submit with Enter key
    await tokenInput.press('Enter');

    // Should trigger form submission
    await expect(page.getByText('Verifying...')).toBeVisible();
  });

  test('should display help text and links', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Verify help text is present
    await expect(page.getByText('How to get a token:')).toBeVisible();

    // Verify GitHub settings link
    const settingsLink = page.getByRole('link', { name: /GitHub Settings/i });
    await expect(settingsLink).toBeVisible();
    await expect(settingsLink).toHaveAttribute('href', /github\.com\/settings\/tokens/);
    await expect(settingsLink).toHaveAttribute('target', '_blank');
  });

  test('should show security notice', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Verify security message
    await expect(
      page.getByText(/Your token is stored securely in your session/)
    ).toBeVisible();
  });
});

test.describe('Authentication API Integration', () => {
  test('should store session in sessionStorage', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Login
    await page.getByLabel('GitHub Personal Access Token').fill(TEST_TOKEN);
    await page.getByRole('button', { name: /verify token/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Check sessionStorage
    const authData = await page.evaluate(() => {
      const auth = sessionStorage.getItem('auth');
      return auth ? JSON.parse(auth) : null;
    });

    expect(authData).not.toBeNull();
    expect(authData).toHaveProperty('sessionId');
    expect(authData).toHaveProperty('user');
  });

  test('should include session ID in API requests', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Login
    await page.getByLabel('GitHub Personal Access Token').fill(TEST_TOKEN);
    await page.getByRole('button', { name: /verify token/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Listen for API requests
    const apiRequest = page.waitForRequest((request) =>
      request.url().includes('/api/v1/')
    );

    // Trigger an API request (e.g., page refresh)
    await page.reload();

    // Verify X-Session-ID header is present
    const request = await apiRequest;
    const headers = request.headers();
    expect(headers['x-session-id']).toBeTruthy();
  });
});
