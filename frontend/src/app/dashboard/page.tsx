/**
 * Dashboard page - Main application interface after authentication.
 * 
 * Displays repositories, features, and workflow interfaces.
 */

'use client';

import { useAuth } from '../../hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Layout from '../../components/Layout';
import Loading from '../../components/Loading';

export default function DashboardPage() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading fullScreen />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome back{user?.login ? `, ${user.login}` : ''}!
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Select a repository to get started with your workflow.
          </p>
        </div>

        {/* Placeholder for repository selection (Phase 4 US1) */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Repository Selection
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Repository selection interface will be implemented in Phase 4 (US1).
          </p>
        </div>
      </div>
    </Layout>
  );
}
