/**
 * Offline Mode Hook
 * React hook for managing offline functionality and graceful degradation
 * Provides offline state, queue management, and cached data access
 */

import { useState, useEffect, useCallback } from 'react';
import { offlineManager, OfflineState, QueuedAction } from '../lib/offline-manager';

export interface UseOfflineModeReturn {
  isOnline: boolean;
  isOffline: boolean;
  connectionQuality: 'good' | 'poor' | 'offline';
  state: OfflineState;
  queuedActions: QueuedAction[];
  queueStats: {
    total: number;
    byType: Record<string, number>;
    byPriority: Record<string, number>;
    oldestAction: Date | null;
  };
  addToQueue: (action: Omit<QueuedAction, 'id' | 'timestamp' | 'retryCount'>) => string;
  removeFromQueue: (id: string) => boolean;
  processQueue: () => Promise<void>;
  clearQueue: () => void;
  cacheData: (key: string, data: any, ttl?: number) => void;
  getCachedData: (key: string) => any | null;
  clearCache: () => void;
}

export const useOfflineMode = (): UseOfflineModeReturn => {
  const [state, setState] = useState<OfflineState>(offlineManager.getState());
  const [queuedActions, setQueuedActions] = useState<QueuedAction[]>(offlineManager.getQueuedActions());
  const [queueStats, setQueueStats] = useState(offlineManager.getQueueStats());

  // Update state when offline manager state changes
  useEffect(() => {
    const unsubscribe = offlineManager.addEventListener((newState: OfflineState) => {
      setState(newState);
      setQueuedActions(offlineManager.getQueuedActions());
      setQueueStats(offlineManager.getQueueStats());
    });

    return unsubscribe;
  }, []);

  // Periodic queue stats update
  useEffect(() => {
    const interval = setInterval(() => {
      setQueuedActions(offlineManager.getQueuedActions());
      setQueueStats(offlineManager.getQueueStats());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const addToQueue = useCallback((action: Omit<QueuedAction, 'id' | 'timestamp' | 'retryCount'>): string => {
    const id = offlineManager.addToQueue(action);
    setQueuedActions(offlineManager.getQueuedActions());
    setQueueStats(offlineManager.getQueueStats());
    return id;
  }, []);

  const removeFromQueue = useCallback((id: string): boolean => {
    const result = offlineManager.removeFromQueue(id);
    if (result) {
      setQueuedActions(offlineManager.getQueuedActions());
      setQueueStats(offlineManager.getQueueStats());
    }
    return result;
  }, []);

  const processQueue = useCallback(async (): Promise<void> => {
    await offlineManager.processQueue();
    setQueuedActions(offlineManager.getQueuedActions());
    setQueueStats(offlineManager.getQueueStats());
  }, []);

  const clearQueue = useCallback((): void => {
    offlineManager.clearQueue();
    setQueuedActions([]);
    setQueueStats(offlineManager.getQueueStats());
  }, []);

  const cacheData = useCallback((key: string, data: any, ttl?: number): void => {
    offlineManager.cacheData(key, data, ttl);
  }, []);

  const getCachedData = useCallback((key: string): any | null => {
    return offlineManager.getCachedData(key);
  }, []);

  const clearCache = useCallback((): void => {
    offlineManager.clearCache();
  }, []);

  return {
    isOnline: state.isOnline,
    isOffline: !state.isOnline,
    connectionQuality: offlineManager.getConnectionQuality(),
    state,
    queuedActions,
    queueStats,
    addToQueue,
    removeFromQueue,
    processQueue,
    clearQueue,
    cacheData,
    getCachedData,
    clearCache
  };
};

// Specialized hooks for common offline scenarios

export const useOfflineUpload = () => {
  const { isOnline, addToQueue, processQueue } = useOfflineMode();

  const queueUpload = useCallback((file: File, endpoint: string = '/api/documents/upload', options: any = {}) => {
    return addToQueue({
      type: 'upload',
      data: { file, endpoint, options },
      maxRetries: 3,
      priority: 'high'
    });
  }, [addToQueue]);

  const processUploads = useCallback(async () => {
    if (isOnline) {
      await processQueue();
    }
  }, [isOnline, processQueue]);

  return {
    isOnline,
    queueUpload,
    processUploads
  };
};

export const useOfflineApiCall = () => {
  const { isOnline, addToQueue, getCachedData, cacheData } = useOfflineMode();

  const makeApiCall = useCallback(async (url: string, options: RequestInit = {}) => {
    if (isOnline) {
      try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        // Cache successful GET requests
        if (options.method === 'GET' || !options.method) {
          cacheData(url, data);
        }
        
        return data;
      } catch (error) {
        // If online but request failed, try cache
        const cachedData = getCachedData(url);
        if (cachedData) {
          return cachedData;
        }
        throw error;
      }
    } else {
      // Offline: try cache first, then queue if it's a mutation
      const cachedData = getCachedData(url);
      if (cachedData && (options.method === 'GET' || !options.method)) {
        return cachedData;
      }
      
      // Queue non-GET requests for later
      if (options.method && options.method !== 'GET') {
        addToQueue({
          type: 'api_call',
          data: { url, options },
          maxRetries: 3,
          priority: 'medium'
        });
        
        throw new Error('Request queued for when connection is restored');
      }
      
      throw new Error('No cached data available and currently offline');
    }
  }, [isOnline, addToQueue, getCachedData, cacheData]);

  return {
    isOnline,
    makeApiCall
  };
};