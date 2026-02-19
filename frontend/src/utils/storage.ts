/**
 * SessionStorage wrapper with type safety and JSON serialization.
 * 
 * Provides:
 * - Type-safe storage operations
 * - Automatic JSON serialization/deserialization
 * - Error handling
 * - Storage event support
 */

export class StorageService {
  /**
   * Get value from sessionStorage.
   * 
   * @param key - Storage key
   * @returns Parsed value or null if not found
   */
  get<T = any>(key: string): T | null {
    try {
      const item = sessionStorage.getItem(key);
      if (!item) return null;
      
      return JSON.parse(item) as T;
    } catch (error) {
      console.error(`Error reading from storage (key: ${key}):`, error);
      return null;
    }
  }

  /**
   * Set value in sessionStorage.
   * 
   * @param key - Storage key
   * @param value - Value to store (will be JSON-serialized)
   */
  set<T = any>(key: string, value: T): void {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error writing to storage (key: ${key}):`, error);
    }
  }

  /**
   * Remove value from sessionStorage.
   * 
   * @param key - Storage key
   */
  remove(key: string): void {
    try {
      sessionStorage.removeItem(key);
    } catch (error) {
      console.error(`Error removing from storage (key: ${key}):`, error);
    }
  }

  /**
   * Clear all values from sessionStorage.
   */
  clear(): void {
    try {
      sessionStorage.clear();
    } catch (error) {
      console.error('Error clearing storage:', error);
    }
  }

  /**
   * Check if key exists in sessionStorage.
   * 
   * @param key - Storage key
   * @returns True if key exists
   */
  has(key: string): boolean {
    return sessionStorage.getItem(key) !== null;
  }

  /**
   * Get all keys in sessionStorage.
   * 
   * @returns Array of storage keys
   */
  keys(): string[] {
    return Object.keys(sessionStorage);
  }
}

// Export singleton instance
export const storage = new StorageService();
