/**
 * Authentication service for managing auth state and session.
 * 
 * Provides:
 * - Authentication state management
 * - Session persistence
 * - Login/logout functionality
 * - User information storage
 */

import { storage } from '../utils/storage';

export interface User {
  id: number;
  login: string;
  name: string;
  email?: string;
  avatar_url: string;
  html_url: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  sessionId: string | null;
  user: User | null;
  tokenPrefix: string | null;
  lastVerified: string | null;
}

const STORAGE_KEY_STATE = 'copilot_auth_state';
const STORAGE_KEY_SESSION = 'copilot_session_id';

class AuthService {
  private state: AuthState;
  private listeners: Set<(state: AuthState) => void> = new Set();

  constructor() {
    this.state = this.loadState();
  }

  /**
   * Load authentication state from storage.
   */
  private loadState(): AuthState {
    const storedState = storage.get<AuthState>(STORAGE_KEY_STATE);
    
    console.debug('[Auth] Loading state from storage:', storedState ? 'Found' : 'Not found');
    
    if (storedState) {
      console.debug('[Auth] Loaded session ID:', storedState.sessionId?.substring(0, 10) + '...');
      return storedState;
    }

    return {
      isAuthenticated: false,
      sessionId: null,
      user: null,
      tokenPrefix: null,
      lastVerified: null,
    };
  }

  /**
   * Save authentication state to storage.
   */
  private saveState(): void {
    storage.set(STORAGE_KEY_STATE, this.state);
    this.notifyListeners();
  }

  /**
   * Subscribe to auth state changes.
   * 
   * @param listener - Callback function
   * @returns Unsubscribe function
   */
  subscribe(listener: (state: AuthState) => void): () => void {
    this.listeners.add(listener);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Notify all listeners of state change.
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.getState());
      } catch (error) {
        console.error('Error in auth state listener:', error);
      }
    });
  }

  /**
   * Get current authentication state.
   */
  getState(): AuthState {
    return { ...this.state };
  }

  /**
   * Set authenticated state.
   * 
   * @param sessionId - Backend session ID
   * @param user - User information
   * @param tokenPrefix - Token prefix for identification
   */
  setAuthenticated(sessionId: string, user: User, tokenPrefix: string): void {
    this.state = {
      isAuthenticated: true,
      sessionId,
      user,
      tokenPrefix,
      lastVerified: new Date().toISOString(),
    };
    
    this.saveState();
  }

  /**
   * Clear authentication state (logout).
   */
  clearAuthentication(): void {
    this.state = {
      isAuthenticated: false,
      sessionId: null,
      user: null,
      tokenPrefix: null,
      lastVerified: null,
    };
    
    storage.clear();
    this.notifyListeners();
  }

  /**
   * Get current session ID.
   */
  getSessionId(): string | null {
    return this.state.sessionId;
  }

  /**
   * Get current user information.
   */
  getUser(): User | null {
    return this.state.user;
  }

  /**
   * Check if user is authenticated.
   */
  isAuthenticated(): boolean {
    return this.state.isAuthenticated && this.state.sessionId !== null;
  }

  /**
   * Get token prefix.
   */
  getTokenPrefix(): string | null {
    return this.state.tokenPrefix;
  }

  /**
   * Update user information.
   * 
   * @param user - Updated user information
   */
  updateUser(user: User): void {
    if (this.state.isAuthenticated) {
      this.state.user = user;
      this.saveState();
    }
  }
}

// Export singleton instance
export const authService = new AuthService();
