/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    // Test environment
    environment: 'jsdom',
    
    // Setup files
    setupFiles: ['./tests/setup.ts'],
    
    // Globals (allows using describe/it/expect without imports)
    globals: true,
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.config.{js,ts}',
        '**/*.d.ts',
        '**/types/',
        '**/__mocks__/',
        'dist/',
        '.next/',
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
    
    // Test inclusion patterns
    include: ['**/*.{test,spec}.{js,jsx,ts,tsx}'],
    
    // Test exclusion patterns
    exclude: [
      'node_modules',
      'dist',
      '.next',
      'tests/e2e',
      '**/*.e2e.{test,spec}.{js,ts}',
    ],
    
    // Mock configuration
    mockReset: true,
    clearMocks: true,
    restoreMocks: true,
    
    // Test timeout (5 seconds)
    testTimeout: 5000,
    
    // Retry failed tests once
    retry: 1,
    
    // Reporter configuration
    reporters: ['verbose'],
    
    // Watch configuration (for development)
    watch: false,
    
    // Pool options
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
      },
    },
  },
  
  // Path resolution (match tsconfig paths)
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
