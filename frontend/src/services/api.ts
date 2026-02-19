/**
 * HTTP API client with authentication and error handling.
 * 
 * Provides:
 * - Axios instance with interceptors
 * - Automatic session ID injection
 * - Error handling and retry logic
 * - Request/response logging
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { authService } from './auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Retry configuration
const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY = 1000; // ms
const MAX_RETRY_DELAY = 10000; // ms

export interface ApiError {
  code: string;
  message: string;
  status: number;
  details?: any;
}

class ApiService {
  private axios: AxiosInstance;
  private retryCount: Map<string, number> = new Map();

  constructor() {
    this.axios = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors.
   */
  private setupInterceptors(): void {
    // Request interceptor - inject session ID
    this.axios.interceptors.request.use(
      (config) => {
        const sessionId = authService.getSessionId();
        
        if (sessionId) {
          config.headers['X-Session-ID'] = sessionId;
        }

        console.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        
        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors
    this.axios.interceptors.response.use(
      (response) => {
        console.debug(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      async (error: AxiosError) => {
        return this.handleError(error);
      }
    );
  }

  /**
   * Handle API errors with retry logic.
   * 
   * @param error - Axios error
   * @returns Promise rejection or retry
   */
  private async handleError(error: AxiosError): Promise<any> {
    const config = error.config as AxiosRequestConfig & { _retry?: number };
    
    // Handle authentication errors
    if (error.response?.status === 401) {
      console.warn('Authentication error - clearing session');
      authService.clearAuthentication();
      
      // Redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      
      return Promise.reject(this.formatError(error));
    }

    // Handle rate limiting
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      const delay = retryAfter ? parseInt(retryAfter) * 1000 : 5000;
      
      console.warn(`Rate limited - retrying after ${delay}ms`);
      
      await this.sleep(delay);
      return this.axios.request(config);
    }

    // Handle retryable errors (5xx, network errors)
    if (this.isRetryableError(error)) {
      const retryKey = `${config.method}_${config.url}`;
      const currentRetry = this.retryCount.get(retryKey) || 0;

      if (currentRetry < MAX_RETRIES) {
        this.retryCount.set(retryKey, currentRetry + 1);
        
        const delay = Math.min(
          INITIAL_RETRY_DELAY * Math.pow(2, currentRetry),
          MAX_RETRY_DELAY
        );
        
        console.warn(`Retrying request (${currentRetry + 1}/${MAX_RETRIES}) after ${delay}ms`);
        
        await this.sleep(delay);
        return this.axios.request(config);
      } else {
        // Max retries exceeded
        this.retryCount.delete(retryKey);
      }
    }

    console.error('API Error:', error);
    return Promise.reject(this.formatError(error));
  }

  /**
   * Check if error is retryable.
   * 
   * @param error - Axios error
   * @returns True if error should be retried
   */
  private isRetryableError(error: AxiosError): boolean {
    // Network errors
    if (!error.response) {
      return true;
    }

    // Server errors (5xx)
    if (error.response.status >= 500) {
      return true;
    }

    // Specific status codes
    if ([408, 429].includes(error.response.status)) {
      return true;
    }

    return false;
  }

  /**
   * Format error into standard ApiError.
   * 
   * @param error - Axios error
   * @returns Formatted API error
   */
  private formatError(error: AxiosError): ApiError {
    if (error.response?.data) {
      const data = error.response.data as any;
      
      if (data.error) {
        return {
          code: data.error.code || 'API_ERROR',
          message: data.error.message || error.message,
          status: error.response.status,
          details: data.error.details,
        };
      }
    }

    return {
      code: error.code || 'NETWORK_ERROR',
      message: error.message || 'An unexpected error occurred',
      status: error.response?.status || 0,
    };
  }

  /**
   * Sleep utility for retry delays.
   * 
   * @param ms - Milliseconds to sleep
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Perform GET request.
   * 
   * @param url - Request URL
   * @param config - Axios config
   * @returns Response data
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axios.get<T>(url, config);
    return response.data;
  }

  /**
   * Perform POST request.
   * 
   * @param url - Request URL
   * @param data - Request body
   * @param config - Axios config
   * @returns Response data
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axios.post<T>(url, data, config);
    return response.data;
  }

  /**
   * Perform PUT request.
   * 
   * @param url - Request URL
   * @param data - Request body
   * @param config - Axios config
   * @returns Response data
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axios.put<T>(url, data, config);
    return response.data;
  }

  /**
   * Perform DELETE request.
   * 
   * @param url - Request URL
   * @param config - Axios config
   * @returns Response data
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axios.delete<T>(url, config);
    return response.data;
  }

  /**
   * Perform PATCH request.
   * 
   * @param url - Request URL
   * @param data - Request body
   * @param config - Axios config
   * @returns Response data
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axios.patch<T>(url, data, config);
    return response.data;
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export type for external use
export type { AxiosRequestConfig };
