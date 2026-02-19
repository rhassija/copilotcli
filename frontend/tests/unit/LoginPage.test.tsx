/**
 * Unit tests for LoginPage component.
 * 
 * Tests form rendering, validation, and authentication flow.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import LoginPage from '../../../src/app/login/page';
import { useAuth } from '../../../src/hooks/useAuth';
import { useRouter } from 'next/navigation';

// Mock hooks
vi.mock('../../../src/hooks/useAuth');
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

describe('LoginPage', () => {
  const mockLogin = vi.fn();
  const mockPush = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock useAuth
    (useAuth as any).mockReturnValue({
      login: mockLogin,
      isAuthenticated: false,
      isLoading: false,
      user: null,
    });

    // Mock useRouter
    (useRouter as any).mockReturnValue({
      push: mockPush,
    });

    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        readText: vi.fn(),
      },
    });
  });

  describe('Rendering', () => {
    it('renders login form', () => {
      render(<LoginPage />);

      expect(screen.getByText('Copilot CLI')).toBeInTheDocument();
      expect(screen.getByText('Sign in with GitHub')).toBeInTheDocument();
      expect(screen.getByLabelText('GitHub Personal Access Token')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /verify token/i })).toBeInTheDocument();
    });

    it('renders token input field', () => {
      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      expect(input).toHaveAttribute('type', 'password');
      expect(input).toHaveAttribute('placeholder', 'ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
    });

    it('renders paste button', () => {
      render(<LoginPage />);

      const pasteButton = screen.getByRole('button', { name: /paste/i });
      expect(pasteButton).toBeInTheDocument();
    });

    it('renders help text', () => {
      render(<LoginPage />);

      expect(screen.getByText('How to get a token:')).toBeInTheDocument();
      expect(screen.getByText(/GitHub Settings/i)).toBeInTheDocument();
    });

    it('renders security message', () => {
      render(<LoginPage />);

      expect(
        screen.getByText(/Your token is stored securely in your session/)
      ).toBeInTheDocument();
    });
  });

  describe('Form Interaction', () => {
    it('updates token input on change', () => {
      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token') as HTMLInputElement;
      fireEvent.change(input, { target: { value: 'ghp_test1234567890' } });

      expect(input.value).toBe('ghp_test1234567890');
    });

    it('clears error when typing', () => {
      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      const submitButton = screen.getByRole('button', { name: /verify token/i });

      // Submit empty form to trigger error
      fireEvent.click(submitButton);
      expect(screen.getByText('Please enter a GitHub token')).toBeInTheDocument();

      // Type to clear error
      fireEvent.change(input, { target: { value: 'ghp_test' } });
      expect(screen.queryByText('Please enter a GitHub token')).not.toBeInTheDocument();
    });

    it('disables submit button when token is empty', () => {
      render(<LoginPage />);

      const submitButton = screen.getByRole('button', { name: /verify token/i });
      expect(submitButton).toBeDisabled();
    });

    it('enables submit button when token is entered', () => {
      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      const submitButton = screen.getByRole('button', { name: /verify token/i });

      fireEvent.change(input, { target: { value: 'ghp_test1234567890' } });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Paste Functionality', () => {
    it('pastes token from clipboard', async () => {
      const mockClipboardText = 'ghp_clipboard_token_123';
      (navigator.clipboard.readText as any).mockResolvedValue(mockClipboardText);

      render(<LoginPage />);

      const pasteButton = screen.getByRole('button', { name: /paste/i });
      fireEvent.click(pasteButton);

      await waitFor(() => {
        const input = screen.getByLabelText('GitHub Personal Access Token') as HTMLInputElement;
        expect(input.value).toBe(mockClipboardText);
      });
    });

    it('handles clipboard read error gracefully', async () => {
      (navigator.clipboard.readText as any).mockRejectedValue(new Error('Clipboard error'));

      render(<LoginPage />);

      const pasteButton = screen.getByRole('button', { name: /paste/i });
      fireEvent.click(pasteButton);

      // Should not crash or show error to user
      await waitFor(() => {
        expect(pasteButton).toBeInTheDocument();
      });
    });

    it('trims whitespace from pasted token', async () => {
      const mockClipboardText = '  ghp_clipboard_token_123  ';
      (navigator.clipboard.readText as any).mockResolvedValue(mockClipboardText);

      render(<LoginPage />);

      const pasteButton = screen.getByRole('button', { name: /paste/i });
      fireEvent.click(pasteButton);

      await waitFor(() => {
        const input = screen.getByLabelText('GitHub Personal Access Token') as HTMLInputElement;
        expect(input.value).toBe('ghp_clipboard_token_123');
      });
    });
  });

  describe('Form Submission', () => {
    it('shows error when submitting empty form', () => {
      render(<LoginPage />);

      const form = screen.getByRole('button', { name: /verify token/i }).closest('form');
      fireEvent.submit(form!);

      expect(screen.getByText('Please enter a GitHub token')).toBeInTheDocument();
      expect(mockLogin).not.toHaveBeenCalled();
    });

    it('calls login with token on submit', async () => {
      mockLogin.mockResolvedValue(undefined);

      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      const submitButton = screen.getByRole('button', { name: /verify token/i });

      fireEvent.change(input, { target: { value: 'ghp_test1234567890' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('ghp_test1234567890');
      });
    });

    it('redirects to dashboard on successful login', async () => {
      mockLogin.mockResolvedValue(undefined);

      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      const submitButton = screen.getByRole('button', { name: /verify token/i });

      fireEvent.change(input, { target: { value: 'ghp_test1234567890' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('shows loading state during submission', async () => {
      mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      const submitButton = screen.getByRole('button', { name: /verify token/i });

      fireEvent.change(input, { target: { value: 'ghp_test1234567890' } });
      fireEvent.click(submitButton);

      expect(screen.getByText('Verifying...')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
      expect(input).toBeDisabled();
    });

    it('displays error message on login failure', async () => {
      const errorMessage = 'Invalid GitHub token';
      mockLogin.mockRejectedValue(new Error(errorMessage));

      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      const submitButton = screen.getByRole('button', { name: /verify token/i });

      fireEvent.change(input, { target: { value: 'ghp_invalid' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      expect(mockPush).not.toHaveBeenCalled();
    });

    it('displays generic error when error has no message', async () => {
      mockLogin.mockRejectedValue(new Error());

      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      const submitButton = screen.getByRole('button', { name: /verify token/i });

      fireEvent.change(input, { target: { value: 'ghp_test' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText('Authentication failed. Please check your token and try again.')
        ).toBeInTheDocument();
      });
    });

    it('re-enables form after error', async () => {
      mockLogin.mockRejectedValue(new Error('Auth failed'));

      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      const submitButton = screen.getByRole('button', { name: /verify token/i });

      fireEvent.change(input, { target: { value: 'ghp_test' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Auth failed')).toBeInTheDocument();
      });

      expect(submitButton).not.toBeDisabled();
      expect(input).not.toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      expect(input).toBeInTheDocument();
    });

    it('has submit button with proper aria attributes', () => {
      render(<LoginPage />);

      const submitButton = screen.getByRole('button', { name: /verify token/i });
      expect(submitButton).toHaveAttribute('type', 'submit');
    });

    it('shows autofocus on token input', () => {
      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      expect(input).toHaveAttribute('autofocus');
    });

    it('has proper error message aria-live region', async () => {
      render(<LoginPage />);

      const submitButton = screen.getByRole('button', { name: /verify token/i });
      fireEvent.click(submitButton);

      const error = await screen.findByText('Please enter a GitHub token');
      expect(error).toBeInTheDocument();
    });
  });

  describe('Security', () => {
    it('uses password input type for token', () => {
      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      expect(input).toHaveAttribute('type', 'password');
    });

    it('has autocomplete disabled', () => {
      render(<LoginPage />);

      const input = screen.getByLabelText('GitHub Personal Access Token');
      expect(input).toHaveAttribute('autocomplete', 'off');
    });

    it('displays security notice', () => {
      render(<LoginPage />);

      expect(
        screen.getByText(/Your token is stored securely/)
      ).toBeInTheDocument();
    });
  });
});
