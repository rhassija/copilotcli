/**
 * Loading spinner component.
 * 
 * Displays animated loading indicator with optional message.
 */

'use client';

interface LoadingProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
  fullScreen?: boolean;
}

/**
 * Loading spinner component.
 */
export default function Loading({ 
  message = 'Loading...', 
  size = 'medium',
  fullScreen = false
}: LoadingProps) {
  const sizeClasses = {
    small: 'w-6 h-6',
    medium: 'w-12 h-12',
    large: 'w-16 h-16',
  };

  const containerClasses = fullScreen
    ? 'fixed inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 z-50'
    : 'flex items-center justify-center p-8';

  return (
    <div className={containerClasses}>
      <div className="flex flex-col items-center space-y-4">
        {/* Animated spinner */}
        <div 
          className={`${sizeClasses[size]} border-4 border-gray-300 border-t-blue-500 rounded-full animate-spin`}
          role="status"
          aria-label="Loading"
        />
        
        {/* Loading message */}
        {message && (
          <p className="text-gray-600 dark:text-gray-300 text-sm font-medium">
            {message}
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * Inline loading spinner (smaller, no message).
 */
export function InlineLoading({ size = 'small' }: { size?: 'small' | 'medium' }) {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-6 h-6',
  };

  return (
    <div 
      className={`${sizeClasses[size]} border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin inline-block`}
      role="status"
      aria-label="Loading"
    />
  );
}
