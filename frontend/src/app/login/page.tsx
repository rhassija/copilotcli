/**
 * Login page for GitHub token authentication.
 * 
 * User enters their GitHub personal access token to authenticate.
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../hooks/useAuth';
import Loading from '../../components/Loading';

export default function LoginPage() {
  const [token, setToken] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token.trim()) {
      setError('Please enter a GitHub token');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await login(token);
      // Redirect to dashboard on success
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your token and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setToken(text.trim());
      setError(null);
    } catch (err) {
      console.error('Failed to read clipboard:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Copilot CLI
          </h1>
          <p className="text-gray-400">
            Web Interface for GitHub Copilot CLI
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Sign in with GitHub
          </h2>

          <form onSubmit={handleSubmit}>
            {/* Token Input */}
            <div className="mb-4">
              <label 
                htmlFor="token" 
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                GitHub Personal Access Token
              </label>
              
              <div className="relative">
                <input
                  id="token"
                  type="password"
                  value={token}
                  onChange={(e) => {
                    setToken(e.target.value);
                    setError(null);
                  }}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400"
                  disabled={isSubmitting}
                  autoComplete="off"
                  autoFocus
                />
                
                {/* Paste Button */}
                <button
                  type="button"
                  onClick={handlePaste}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 focus:outline-none"
                  disabled={isSubmitting}
                >
                  Paste
                </button>
              </div>

              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Your token is stored securely in your session and never sent to external servers.
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                <p className="text-sm text-red-600 dark:text-red-400">
                  {error}
                </p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || !token.trim()}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center space-x-2">
                  <Loading size="small" />
                  <span>Verifying...</span>
                </span>
              ) : (
                'Verify Token'
              )}
            </button>
          </form>

          {/* Help Text */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
              How to get a token:
            </h3>
            <ol className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-decimal list-inside">
              <li>Go to <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">GitHub Settings → Developer settings → Personal access tokens</a></li>
              <li>Click "Generate new token (classic)"</li>
              <li>Select scopes: <code className="bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded">repo</code>, <code className="bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded">user</code></li>
              <li>Copy the token and paste it above</li>
            </ol>
          </div>
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-sm text-gray-400">
          Powered by GitHub Copilot CLI
        </p>
      </div>
    </div>
  );
}
