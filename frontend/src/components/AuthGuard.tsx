/**
 * Auth guard component to protect routes that require authentication.
 * 
 * Redirects to login if user is not authenticated.
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../hooks/useAuth';
import Loading from './Loading';

interface AuthGuardProps {
  children: React.ReactNode;
  loginPath?: string;
}

/**
 * Wrapper component that requires authentication.
 * 
 * If user is not authenticated, redirects to login page.
 * While checking auth, displays loading spinner.
 */
export default function AuthGuard({ 
  children, 
  loginPath = '/login' 
}: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If not loading and not authenticated, redirect to login
    if (!isLoading && !isAuthenticated) {
      console.log('Not authenticated - redirecting to login');
      router.push(loginPath);
    }
  }, [isAuthenticated, isLoading, router, loginPath]);

  // Show loading while checking auth
  if (isLoading) {
    return <Loading message="Verifying authentication..." />;
  }

  // Show nothing if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // Render children if authenticated
  return <>{children}</>;
}
