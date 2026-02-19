/**
 * React hook for API data fetching with loading and error states.
 * 
 * Provides:
 * - Automatic data fetching
 * - Loading and error state management
 * - Manual refetch function
 * - Automatic cleanup
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiService, type AxiosRequestConfig } from '../services/api';

export interface UseApiOptions<T> {
  /**
   * Initial data value
   */
  initialData?: T;
  
  /**
   * Whether to fetch immediately on mount
   */
  immediate?: boolean;
  
  /**
   * Axios request config
   */
  config?: AxiosRequestConfig;
  
  /**
   * Callback on successful fetch
   */
  onSuccess?: (data: T) => void;
  
  /**
   * Callback on error
   */
  onError?: (error: any) => void;
}

export interface UseApiReturn<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  mutate: (newData: T) => void;
}

/**
 * Hook for fetching data from API with loading/error states.
 * 
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @returns API data, loading state, error, and refetch function
 */
export function useApi<T = any>(
  url: string,
  options: UseApiOptions<T> = {}
): UseApiReturn<T> {
  const {
    initialData = null,
    immediate = true,
    config,
    onSuccess,
    onError,
  } = options;

  const [data, setData] = useState<T | null>(initialData);
  const [isLoading, setIsLoading] = useState(immediate);
  const [error, setError] = useState<string | null>(null);
  
  // Track if component is mounted to prevent state updates after unmount
  const isMounted = useRef(true);

  /**
   * Fetch data from API.
   */
  const fetchData = useCallback(async () => {
    if (!isMounted.current) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiService.get<T>(url, config);
      
      if (!isMounted.current) return;

      setData(response);
      
      if (onSuccess) {
        onSuccess(response);
      }
    } catch (err: any) {
      if (!isMounted.current) return;

      const errorMessage = err.message || 'Failed to fetch data';
      setError(errorMessage);
      
      if (onError) {
        onError(err);
      }
      
      console.error('API fetch error:', err);
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, [url, config, onSuccess, onError]);

  /**
   * Manually update data without refetching.
   * 
   * @param newData - New data value
   */
  const mutate = useCallback((newData: T) => {
    setData(newData);
  }, []);

  // Fetch data on mount if immediate is true
  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, [immediate, fetchData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
    mutate,
  };
}

/**
 * Hook for POST requests with loading/error states.
 * 
 * @param url - API endpoint URL
 * @returns Post function, loading state, and error
 */
export function useApiPost<TRequest = any, TResponse = any>(
  url: string
): {
  post: (data: TRequest) => Promise<TResponse>;
  isLoading: boolean;
  error: string | null;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isMounted = useRef(true);

  const post = useCallback(async (data: TRequest): Promise<TResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiService.post<TResponse>(url, data);
      
      if (!isMounted.current) {
        throw new Error('Component unmounted');
      }

      return response;
    } catch (err: any) {
      if (!isMounted.current) {
        throw err;
      }

      const errorMessage = err.message || 'POST request failed';
      setError(errorMessage);
      throw err;
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, [url]);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  return { post, isLoading, error };
}
