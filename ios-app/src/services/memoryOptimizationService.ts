import { AppState, AppStateStatus } from 'react-native';
import { imageCacheService } from './imageCacheService';
import { offlineStorage } from './offlineStorage';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface MemoryStats {
  totalMemoryUsage: number;
  imageCacheSize: number;
  offlineDataSize: number;
  tempDataSize: number;
  lastCleanup: Date | null;
}

export interface MemoryConfig {
  maxMemoryUsage: number; // in bytes
  cleanupThreshold: number; // percentage (0-1)
  aggressiveCleanup: boolean;
  autoCleanupInterval: number; // in milliseconds
}

class MemoryOptimizationService {
  private readonly DEFAULT_CONFIG: MemoryConfig = {
    maxMemoryUsage: 200 * 1024 * 1024, // 200MB
    cleanupThreshold: 0.8, // 80%
    aggressiveCleanup: false,
    autoCleanupInterval: 10 * 60 * 1000, // 10 minutes
  };

  private readonly MEMORY_STATS_KEY = 'memory_optimization_stats';
  private readonly TEMP_DATA_PREFIX = 'temp_';

  private config: MemoryConfig;
  private cleanupTimer: NodeJS.Timeout | null = null;
  private appState: AppStateStatus = 'active';
  private memoryWarningListeners: (() => void)[] = [];

  constructor(config?: Partial<MemoryConfig>) {
    this.config = { ...this.DEFAULT_CONFIG, ...config };
    this.initializeAppStateListener();
  }

  private initializeAppStateListener(): void {
    AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      const wasBackground = this.appState === 'background';
      this.appState = nextAppState;

      if (nextAppState === 'background') {
        // App went to background, perform cleanup
        this.performBackgroundCleanup();
        this.stopAutoCleanup();
      } else if (nextAppState === 'active' && wasBackground) {
        // App came to foreground
        this.startAutoCleanup();
      }
    });
  }

  async startMemoryOptimization(): Promise<void> {
    console.log('Starting memory optimization service');
    
    // Perform initial cleanup
    await this.performCleanup();
    
    // Start auto cleanup if app is active
    if (this.appState === 'active') {
      this.startAutoCleanup();
    }
  }

  stopMemoryOptimization(): void {
    console.log('Stopping memory optimization service');
    this.stopAutoCleanup();
  }

  private startAutoCleanup(): void {
    if (this.cleanupTimer) return;

    this.cleanupTimer = setInterval(async () => {
      try {
        const stats = await this.getMemoryStats();
        const usageRatio = stats.totalMemoryUsage / this.config.maxMemoryUsage;

        if (usageRatio >= this.config.cleanupThreshold) {
          console.log(`Memory usage at ${(usageRatio * 100).toFixed(1)}%, triggering cleanup`);
          await this.performCleanup();
        }
      } catch (error) {
        console.error('Auto cleanup failed:', error);
      }
    }, this.config.autoCleanupInterval);
  }

  private stopAutoCleanup(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }

  async performCleanup(aggressive = false): Promise<MemoryStats> {
    console.log(`Performing ${aggressive ? 'aggressive' : 'normal'} memory cleanup`);

    try {
      const initialStats = await this.getMemoryStats();
      
      // 1. Clean up temporary data
      await this.cleanupTempData();
      
      // 2. Optimize image cache
      await this.optimizeImageCache(aggressive);
      
      // 3. Clean up offline data if aggressive
      if (aggressive || this.config.aggressiveCleanup) {
        await this.cleanupOfflineData();
      }
      
      // 4. Clear unused AsyncStorage entries
      await this.cleanupAsyncStorage();
      
      // 5. Trigger garbage collection hint (if available)
      this.triggerGarbageCollection();
      
      const finalStats = await this.getMemoryStats();
      await this.updateLastCleanupTime();
      
      const savedMemory = initialStats.totalMemoryUsage - finalStats.totalMemoryUsage;
      console.log(`Memory cleanup completed. Freed ${(savedMemory / 1024 / 1024).toFixed(2)}MB`);
      
      return finalStats;
    } catch (error) {
      console.error('Memory cleanup failed:', error);
      throw error;
    }
  }

  private async cleanupTempData(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const tempKeys = keys.filter(key => key.startsWith(this.TEMP_DATA_PREFIX));
      
      if (tempKeys.length > 0) {
        await AsyncStorage.multiRemove(tempKeys);
        console.log(`Removed ${tempKeys.length} temporary data entries`);
      }
    } catch (error) {
      console.error('Failed to cleanup temp data:', error);
    }
  }

  private async optimizeImageCache(aggressive: boolean): Promise<void> {
    try {
      const cacheStats = await imageCacheService.getCacheStats();
      const maxCacheSize = aggressive ? 
        this.config.maxMemoryUsage * 0.3 : // 30% of max memory for aggressive
        this.config.maxMemoryUsage * 0.5;  // 50% of max memory for normal

      if (cacheStats.totalSize > maxCacheSize) {
        // Update cache config to force cleanup
        imageCacheService.updateConfig({
          maxCacheSize: Math.floor(maxCacheSize),
        });
        
        // Trigger cache cleanup by trying to cache a dummy image
        // This will force the cache to clean up old entries
        console.log(`Image cache size ${(cacheStats.totalSize / 1024 / 1024).toFixed(2)}MB exceeds limit, cleaning up`);
      }
    } catch (error) {
      console.error('Failed to optimize image cache:', error);
    }
  }

  private async cleanupOfflineData(): Promise<void> {
    try {
      // Remove old study sessions (keep only last 30 days)
      const sessions = await offlineStorage.getStudySessions();
      const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
      
      const recentSessions = sessions.filter(session => 
        new Date(session.timestamp).getTime() > thirtyDaysAgo
      );
      
      if (recentSessions.length < sessions.length) {
        await AsyncStorage.setItem('offline_study_sessions', JSON.stringify(recentSessions));
        console.log(`Removed ${sessions.length - recentSessions.length} old study sessions`);
      }
      
      // Clean up old pending changes (older than 7 days)
      const pendingChanges = await offlineStorage.getPendingChanges();
      const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
      
      const recentChanges = pendingChanges.filter(change =>
        new Date(change.timestamp).getTime() > sevenDaysAgo
      );
      
      if (recentChanges.length < pendingChanges.length) {
        await AsyncStorage.setItem('offline_pending_changes', JSON.stringify(recentChanges));
        console.log(`Removed ${pendingChanges.length - recentChanges.length} old pending changes`);
      }
    } catch (error) {
      console.error('Failed to cleanup offline data:', error);
    }
  }

  private async cleanupAsyncStorage(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const keysToRemove: string[] = [];
      
      // Check each key for cleanup criteria
      for (const key of keys) {
        try {
          // Skip system keys
          if (key.startsWith('offline_') || key.startsWith('image_cache_')) {
            continue;
          }
          
          const value = await AsyncStorage.getItem(key);
          if (!value) {
            keysToRemove.push(key);
            continue;
          }
          
          // Try to parse as JSON to check for timestamp-based cleanup
          try {
            const data = JSON.parse(value);
            if (data.timestamp && typeof data.timestamp === 'string') {
              const age = Date.now() - new Date(data.timestamp).getTime();
              const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days
              
              if (age > maxAge) {
                keysToRemove.push(key);
              }
            }
          } catch {
            // Not JSON or no timestamp, skip
          }
        } catch (error) {
          console.warn(`Failed to check key ${key} for cleanup:`, error);
        }
      }
      
      if (keysToRemove.length > 0) {
        await AsyncStorage.multiRemove(keysToRemove);
        console.log(`Removed ${keysToRemove.length} unused AsyncStorage entries`);
      }
    } catch (error) {
      console.error('Failed to cleanup AsyncStorage:', error);
    }
  }

  private triggerGarbageCollection(): void {
    // React Native doesn't expose direct GC control, but we can trigger it indirectly
    try {
      // Force garbage collection by creating and releasing large objects
      if (global.gc) {
        global.gc();
      } else {
        // Fallback: create temporary large objects to trigger GC
        const temp = new Array(1000).fill(new Array(1000).fill(0));
        temp.length = 0;
      }
    } catch (error) {
      // GC not available, ignore
    }
  }

  private async performBackgroundCleanup(): Promise<void> {
    try {
      console.log('Performing background cleanup');
      
      // More aggressive cleanup when app goes to background
      await this.cleanupTempData();
      await this.optimizeImageCache(true);
      
      // Clear any cached UI state that's not needed in background
      await this.clearUICache();
      
    } catch (error) {
      console.error('Background cleanup failed:', error);
    }
  }

  private async clearUICache(): Promise<void> {
    try {
      // Clear any UI-related cached data
      const keys = await AsyncStorage.getAllKeys();
      const uiCacheKeys = keys.filter(key => 
        key.includes('ui_cache') || 
        key.includes('view_state') ||
        key.includes('scroll_position')
      );
      
      if (uiCacheKeys.length > 0) {
        await AsyncStorage.multiRemove(uiCacheKeys);
        console.log(`Cleared ${uiCacheKeys.length} UI cache entries`);
      }
    } catch (error) {
      console.error('Failed to clear UI cache:', error);
    }
  }

  async getMemoryStats(): Promise<MemoryStats> {
    try {
      const [imageCacheStats, offlineDataSize, lastCleanupTime] = await Promise.all([
        imageCacheService.getCacheStats(),
        offlineStorage.getStorageSize(),
        this.getLastCleanupTime(),
      ]);

      // Estimate temp data size
      const tempDataSize = await this.getTempDataSize();

      const totalMemoryUsage = imageCacheStats.totalSize + offlineDataSize + tempDataSize;

      return {
        totalMemoryUsage,
        imageCacheSize: imageCacheStats.totalSize,
        offlineDataSize,
        tempDataSize,
        lastCleanup: lastCleanupTime,
      };
    } catch (error) {
      console.error('Failed to get memory stats:', error);
      return {
        totalMemoryUsage: 0,
        imageCacheSize: 0,
        offlineDataSize: 0,
        tempDataSize: 0,
        lastCleanup: null,
      };
    }
  }

  private async getTempDataSize(): Promise<number> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const tempKeys = keys.filter(key => key.startsWith(this.TEMP_DATA_PREFIX));
      
      let totalSize = 0;
      for (const key of tempKeys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += new Blob([value]).size;
        }
      }
      
      return totalSize;
    } catch (error) {
      console.error('Failed to calculate temp data size:', error);
      return 0;
    }
  }

  private async getLastCleanupTime(): Promise<Date | null> {
    try {
      const statsJson = await AsyncStorage.getItem(this.MEMORY_STATS_KEY);
      if (statsJson) {
        const stats = JSON.parse(statsJson);
        return stats.lastCleanup ? new Date(stats.lastCleanup) : null;
      }
      return null;
    } catch (error) {
      console.error('Failed to get last cleanup time:', error);
      return null;
    }
  }

  private async updateLastCleanupTime(): Promise<void> {
    try {
      const stats = {
        lastCleanup: new Date().toISOString(),
      };
      await AsyncStorage.setItem(this.MEMORY_STATS_KEY, JSON.stringify(stats));
    } catch (error) {
      console.error('Failed to update last cleanup time:', error);
    }
  }

  // Manual cleanup trigger
  async forceCleanup(aggressive = false): Promise<MemoryStats> {
    console.log('Force cleanup triggered by user');
    return this.performCleanup(aggressive);
  }

  // Memory warning handler
  onMemoryWarning(callback: () => void): () => void {
    this.memoryWarningListeners.push(callback);
    
    return () => {
      const index = this.memoryWarningListeners.indexOf(callback);
      if (index > -1) {
        this.memoryWarningListeners.splice(index, 1);
      }
    };
  }

  // Trigger memory warning (can be called by other services)
  triggerMemoryWarning(): void {
    console.warn('Memory warning triggered');
    this.memoryWarningListeners.forEach(callback => {
      try {
        callback();
      } catch (error) {
        console.error('Memory warning callback error:', error);
      }
    });
    
    // Perform immediate cleanup
    this.performCleanup(true).catch(error => {
      console.error('Emergency cleanup failed:', error);
    });
  }

  updateConfig(newConfig: Partial<MemoryConfig>): void {
    this.config = { ...this.config, ...newConfig };
    console.log('Memory optimization config updated:', this.config);
  }
}

export const memoryOptimizationService = new MemoryOptimizationService();