import AsyncStorage from '@react-native-async-storage/async-storage';
import RNFS from 'react-native-fs';
import { Platform } from 'react-native';

export interface CacheConfig {
  maxCacheSize: number; // in bytes
  maxCacheAge: number; // in milliseconds
  compressionQuality: number; // 0-1
}

export interface CacheEntry {
  url: string;
  localPath: string;
  size: number;
  timestamp: number;
  accessCount: number;
  lastAccessed: number;
}

class ImageCacheService {
  private readonly CACHE_DIR = `${RNFS.CachesDirectoryPath}/images`;
  private readonly CACHE_INDEX_KEY = 'image_cache_index';
  private readonly DEFAULT_CONFIG: CacheConfig = {
    maxCacheSize: 100 * 1024 * 1024, // 100MB
    maxCacheAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    compressionQuality: 0.8,
  };

  private config: CacheConfig;
  private cacheIndex: Map<string, CacheEntry> = new Map();
  private initialized = false;

  constructor(config?: Partial<CacheConfig>) {
    this.config = { ...this.DEFAULT_CONFIG, ...config };
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Create cache directory if it doesn't exist
      const dirExists = await RNFS.exists(this.CACHE_DIR);
      if (!dirExists) {
        await RNFS.mkdir(this.CACHE_DIR);
      }

      // Load cache index
      await this.loadCacheIndex();
      
      // Clean up expired entries
      await this.cleanupExpiredEntries();
      
      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize image cache:', error);
      throw error;
    }
  }

  private async loadCacheIndex(): Promise<void> {
    try {
      const indexJson = await AsyncStorage.getItem(this.CACHE_INDEX_KEY);
      if (indexJson) {
        const indexArray: [string, CacheEntry][] = JSON.parse(indexJson);
        this.cacheIndex = new Map(indexArray);
      }
    } catch (error) {
      console.error('Failed to load cache index:', error);
      this.cacheIndex = new Map();
    }
  }

  private async saveCacheIndex(): Promise<void> {
    try {
      const indexArray = Array.from(this.cacheIndex.entries());
      await AsyncStorage.setItem(this.CACHE_INDEX_KEY, JSON.stringify(indexArray));
    } catch (error) {
      console.error('Failed to save cache index:', error);
    }
  }

  private generateCacheKey(url: string): string {
    // Simple hash function for URL
    let hash = 0;
    for (let i = 0; i < url.length; i++) {
      const char = url.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }

  private getCacheFilePath(cacheKey: string, url: string): string {
    const extension = url.split('.').pop()?.toLowerCase() || 'jpg';
    return `${this.CACHE_DIR}/${cacheKey}.${extension}`;
  }

  async getCachedImage(url: string): Promise<string | null> {
    await this.initialize();

    const cacheKey = this.generateCacheKey(url);
    const entry = this.cacheIndex.get(cacheKey);

    if (!entry) {
      return null;
    }

    // Check if file still exists
    const fileExists = await RNFS.exists(entry.localPath);
    if (!fileExists) {
      this.cacheIndex.delete(cacheKey);
      await this.saveCacheIndex();
      return null;
    }

    // Check if entry is expired
    const now = Date.now();
    if (now - entry.timestamp > this.config.maxCacheAge) {
      await this.removeCacheEntry(cacheKey);
      return null;
    }

    // Update access statistics
    entry.accessCount++;
    entry.lastAccessed = now;
    await this.saveCacheIndex();

    return Platform.OS === 'ios' ? `file://${entry.localPath}` : entry.localPath;
  }

  async cacheImage(url: string): Promise<string> {
    await this.initialize();

    const cacheKey = this.generateCacheKey(url);
    const existingEntry = this.cacheIndex.get(cacheKey);

    // Return existing cached image if available
    if (existingEntry) {
      const cachedPath = await this.getCachedImage(url);
      if (cachedPath) {
        return cachedPath;
      }
    }

    try {
      const localPath = this.getCacheFilePath(cacheKey, url);
      
      // Download image
      const downloadResult = await RNFS.downloadFile({
        fromUrl: url,
        toFile: localPath,
        background: true,
        discretionary: true,
        cacheable: false,
      }).promise;

      if (downloadResult.statusCode !== 200) {
        throw new Error(`Failed to download image: ${downloadResult.statusCode}`);
      }

      // Get file size
      const fileStats = await RNFS.stat(localPath);
      const fileSize = fileStats.size;

      // Check cache size limits
      await this.ensureCacheSize(fileSize);

      // Create cache entry
      const entry: CacheEntry = {
        url,
        localPath,
        size: fileSize,
        timestamp: Date.now(),
        accessCount: 1,
        lastAccessed: Date.now(),
      };

      this.cacheIndex.set(cacheKey, entry);
      await this.saveCacheIndex();

      return Platform.OS === 'ios' ? `file://${localPath}` : localPath;
    } catch (error) {
      console.error('Failed to cache image:', error);
      throw error;
    }
  }

  private async ensureCacheSize(newFileSize: number): Promise<void> {
    const currentSize = this.getCurrentCacheSize();
    const targetSize = this.config.maxCacheSize - newFileSize;

    if (currentSize <= targetSize) {
      return;
    }

    // Sort entries by LRU (least recently used)
    const entries = Array.from(this.cacheIndex.entries()).sort(([, a], [, b]) => {
      // Prioritize by last accessed time, then by access count
      const timeDiff = a.lastAccessed - b.lastAccessed;
      if (timeDiff !== 0) return timeDiff;
      return a.accessCount - b.accessCount;
    });

    let freedSize = 0;
    for (const [cacheKey, entry] of entries) {
      if (currentSize - freedSize <= targetSize) {
        break;
      }

      await this.removeCacheEntry(cacheKey);
      freedSize += entry.size;
    }
  }

  private getCurrentCacheSize(): number {
    return Array.from(this.cacheIndex.values()).reduce((total, entry) => total + entry.size, 0);
  }

  private async removeCacheEntry(cacheKey: string): Promise<void> {
    const entry = this.cacheIndex.get(cacheKey);
    if (!entry) return;

    try {
      const fileExists = await RNFS.exists(entry.localPath);
      if (fileExists) {
        await RNFS.unlink(entry.localPath);
      }
    } catch (error) {
      console.error('Failed to remove cache file:', error);
    }

    this.cacheIndex.delete(cacheKey);
    await this.saveCacheIndex();
  }

  private async cleanupExpiredEntries(): Promise<void> {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [cacheKey, entry] of this.cacheIndex.entries()) {
      if (now - entry.timestamp > this.config.maxCacheAge) {
        expiredKeys.push(cacheKey);
      }
    }

    for (const cacheKey of expiredKeys) {
      await this.removeCacheEntry(cacheKey);
    }
  }

  async preloadImages(urls: string[]): Promise<void> {
    await this.initialize();

    const preloadPromises = urls.map(async (url) => {
      try {
        const cached = await this.getCachedImage(url);
        if (!cached) {
          await this.cacheImage(url);
        }
      } catch (error) {
        console.warn('Failed to preload image:', url, error);
      }
    });

    await Promise.allSettled(preloadPromises);
  }

  async getCacheStats(): Promise<{
    totalSize: number;
    entryCount: number;
    oldestEntry: number;
    newestEntry: number;
  }> {
    await this.initialize();

    const entries = Array.from(this.cacheIndex.values());
    const totalSize = entries.reduce((sum, entry) => sum + entry.size, 0);
    const timestamps = entries.map(entry => entry.timestamp);

    return {
      totalSize,
      entryCount: entries.length,
      oldestEntry: timestamps.length > 0 ? Math.min(...timestamps) : 0,
      newestEntry: timestamps.length > 0 ? Math.max(...timestamps) : 0,
    };
  }

  async clearCache(): Promise<void> {
    await this.initialize();

    try {
      // Remove all cache files
      const dirExists = await RNFS.exists(this.CACHE_DIR);
      if (dirExists) {
        await RNFS.unlink(this.CACHE_DIR);
        await RNFS.mkdir(this.CACHE_DIR);
      }

      // Clear cache index
      this.cacheIndex.clear();
      await AsyncStorage.removeItem(this.CACHE_INDEX_KEY);
    } catch (error) {
      console.error('Failed to clear cache:', error);
      throw error;
    }
  }

  updateConfig(newConfig: Partial<CacheConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

export const imageCacheService = new ImageCacheService();