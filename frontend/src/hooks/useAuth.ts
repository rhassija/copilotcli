/**
 * React hook for authentication state management.
 * 
 * Provides:
 * - Authentication state access
 * - Login/logout functions
 * - Automatic state updates via subscription
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { authService, type User, type AuthState } from '../services/auth';
import { apiService } from '../services/api';

export interface UseAuthReturn {
  isAuthenticated: boolean;
  user: User | null;
  sessionId: string | null;
  tokenPrefix: string | null;
  login: (token: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook for accessing and managing authentication state.
 */
export function useAuth(): UseAuthReturn {
  const [state, setState] = useState<AuthState>(authService.getState());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Subscribe to auth state changes
  useEffect(() => {
    const unsubscribe = authService.subscribe((newState) => {
      setState(newState);
    });

    return unsubscribe;
  }, []);

  /**
   * Login with GitHub token.
   * 
   * @param token - GitHub personal access token
   */
  const login = useCallback(async (token: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Call backend auth endpoint
      const response = await apiService.post<{
        session_id: string;
        user: User;
        token_prefix: string;
      }>('/auth/login', { token });

      // Update auth state
      authService.setAuthenticated(
        response.session_id,
        response.user,
        response.token_prefix
      );

      console.log('Login successful:', response.user.login);
    } catch (err: any) {
      const errorMessage = err.message || 'Login failed';
      setError(errorMessage);
      console.error('Login error:', err);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Logout and clear session.
   */
  const logout = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const sessionId = authService.getSessionId();
      
      if (sessionId) {
        // Call backend logout endpoint
        await apiService.post('/auth/logout', { session_id: sessionId });
      }

      // Clear local auth state
      authService.clearAuthentication();

      console.log('Logout successful');
    } catch (err: any) {
      console.error('Logout error:', err);
      // Clear auth state even if backend call fails
      authService.clearAuthentication();
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Refresh authentication by verifying session.
   */
  const refreshAuth = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const sessionId = authService.getSessionId();
      
      if (!sessionId) {
        throw new Error('No active session');
      }

      // Verify session with backend
      const response = await apiService.get<{
        user: User;
        session_valid: boolean;
      }>('/auth/verify');

      if (response.session_valid) {
        // Update user information
        authService.updateUser(response.user);
        console.log('Auth refreshed successfully');
      } else {
        throw new Error('Session expired');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Auth refresh failed';
      setError(errorMessage);
      console.error('Auth refresh error:', err);
      
      // Clear auth on failure
      authService.clearAuthentication();
      
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isAuthenticated: state.isAuthenticated,
    user: state.user,
    sessionId: state.sessionId,
    tokenPrefix: state.tokenPrefix,
    login,
    logout,
    refreshAuth,
    isLoading,
    error,
  };
}
