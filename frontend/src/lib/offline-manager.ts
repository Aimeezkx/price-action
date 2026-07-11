/**
 * Offline Manager
 * Handles offline mode detection and graceful degradation
 * Manages local storage for failed uploads and retry queue
 */

export interface OfflineState {
  isOnline: boolean;
  lastOnlineTime: Date | null;
  connectionType: 'online' | 'offline' | 'slow' | 'unstable';
  networkSpeed: number | null; // Mbps
}

export interface QueuedAction {
  id: string;
  type: 'upload' | 'api_call' | 'sync';
  data: any;
  timestamp: Date;
  retryCount: number;
  maxRetries: number;
  priority: 'low' | 'medium' | 'high';
}

export interface OfflineStorage {
  queuedActions: QueuedAction[];
  cachedData: Record<string, any>;
  userPreferences: Record<string, any>;
}

export class OfflineManager {
  private state: OfflineState = {
    isOnline: navigator.onLine,
    lastOnlineTime: navigator.onLine ? new Date() : null,
    connectionType: navigator.onLine ? 'online' : 'offline',
    networkSpeed: null
  };

  private listeners: Array<(state: OfflineState) => void> = [];
  private actionQueue: QueuedAction[] = [];
  private storageKey = 'offline_manager_data';
  private connectionCheckInterval: NodeJS.Timeout | null = null;
  private speedTestInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.initializeEventListeners();
    this.loadFromStorage();
    this.startConnectionMonitoring();
  }

  public getState(): OfflineState {
    return { ...this.state };
  }

  public isOnline(): boolean {
    return this.state.isOnline;
  }

  public isOffline(): boolean {
    return !this.state.isOnline;
  }

  public getConnectionQuality(): 'good' | 'poor' | 'offline' {
    if (!this.state.isOnline) return 'offline';
    if (this.state.connectionType === 'slow' || this.state.connectionType === 'unstable') {
      return 'poor';
    }
    return 'good';
  }

  public addToQueue(action: Omit<QueuedAction, 'id' | 'timestamp' | 'retryCount'>): string {
    const queuedAction: QueuedAction = {
      ...action,
      id: this.generateActionId(),
      timestamp: new Date(),
      retryCount: 0
    };

    this.actionQueue.push(queuedAction);
    this.saveToStorage();

    // Try to process immediately if online
    if (this.state.isOnline) {
      this.processQueue();
    }

    return queuedAction.id;
  }

  public removeFromQueue(id: string): boolean {
    const index = this.actionQueue.findIndex(action => action.id === id);
    if (index > -1) {
      this.actionQueue.splice(index, 1);
      this.saveToStorage();
      return true;
    }
    return false;
  }

  public getQueuedActions(): QueuedAction[] {
    return [...this.actionQueue];
  }

  public getQueueStats(): {
    total: number;
    byType: Record<string, number>;
    byPriority: Record<string, number>;
    oldestAction: Date | null;
  } {
    const byType: Record<string, number> = {};
    const byPriority: Record<string, number> = {};
    let oldestAction: Date | null = null;

    this.actionQueue.forEach(action => {
      byType[action.type] = (byType[action.type] || 0) + 1;
      byPriority[action.priority] = (byPriority[action.priority] || 0) + 1;

      if (!oldestAction || action.timestamp < oldestAction) {
        oldestAction = action.timestamp;
      }
    });

    return {
      total: this.actionQueue.length,
      byType,
      byPriority,
      oldestAction
    };
  }

  public clearQueue(): void {
    this.actionQueue = [];
    this.saveToStorage();
  }

  public addEventListener(listener: (state: OfflineState) => void): () => void {
    this.listeners.push(listener);

    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  public async processQueue(): Promise<void> {
    if (!this.state.isOnline || this.actionQueue.length === 0) {
      return;
    }

    // Sort by priority and timestamp
    const sortedActions = [...this.actionQueue].sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      const aPriority = priorityOrder[a.priority];
      const bPriority = priorityOrder[b.priority];

      if (aPriority !== bPriority) {
        return bPriority - aPriority;
      }

      return a.timestamp.getTime() - b.timestamp.getTime();
    });

    const processedIds: string[] = [];

    for (const action of sortedActions) {
      try {
        await this.processAction(action);
        processedIds.push(action.id);
      } catch (error) {
        action.retryCount++;

        if (action.retryCount >= action.maxRetries) {
          processedIds.push(action.id);
          console.error(`Action ${action.id} failed after ${action.maxRetries} retries:`, error);
        }
      }
    }

    // Remove processed actions
    processedIds.forEach(id => this.removeFromQueue(id));
  }

  public cacheData(key: string, data: any, ttl?: number): void {
    const storage = this.getStorage();
    const cacheEntry = {
      data,
      timestamp: Date.now(),
      ttl: ttl || (24 * 60 * 60 * 1000) // 24 hours default
    };

    storage.cachedData[key] = cacheEntry;
    this.saveStorage(storage);
  }

  public getCachedData(key: string): any | null {
    const storage = this.getStorage();
    const cacheEntry = storage.cachedData[key];

    if (!cacheEntry) return null;

    // Check if expired
    if (Date.now() - cacheEntry.timestamp > cacheEntry.ttl) {
      delete storage.cachedData[key];
      this.saveStorage(storage);
      return null;
    }

    return cacheEntry.data;
  }

  public clearCache(): void {
    const storage = this.getStorage();
    storage.cachedData = {};
    this.saveStorage(storage);
  }

  private initializeEventListeners(): void {
    window.addEventListener('online', this.handleOnline.bind(this));
    window.addEventListener('offline', this.handleOffline.bind(this));

    // Listen for connection changes
    if ('connection' in navigator) {
      (navigator as any).connection.addEventListener('change', this.handleConnectionChange.bind(this));
    }
  }

  private handleOnline(): void {
    this.state.isOnline = true;
    this.state.lastOnlineTime = new Date();
    this.state.connectionType = 'online';

    this.notifyListeners();
    this.processQueue();
  }

  private handleOffline(): void {
    this.state.isOnline = false;
    this.state.connectionType = 'offline';
    this.state.networkSpeed = null;

    this.notifyListeners();
  }

  private handleConnectionChange(): void {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;

      // Update connection type based on effective type
      if (connection.effectiveType) {
        switch (connection.effectiveType) {
          case 'slow-2g':
          case '2g':
            this.state.connectionType = 'slow';
            break;
          case '3g':
            this.state.connectionType = 'unstable';
            break;
          case '4g':
          default:
            this.state.connectionType = 'online';
            break;
        }
      }

      // Update network speed estimate
      if (connection.downlink) {
        this.state.networkSpeed = connection.downlink;
      }

      this.notifyListeners();
    }
  }

  private startConnectionMonitoring(): void {
    // Periodic connection quality check
    this.connectionCheckInterval = setInterval(() => {
      this.checkConnectionQuality();
    }, 30000); // Check every 30 seconds

    // Periodic speed test
    this.speedTestInterval = setInterval(() => {
      if (this.state.isOnline) {
        this.performSpeedTest();
      }
    }, 300000); // Test every 5 minutes
  }

  private async checkConnectionQuality(): Promise<void> {
    if (!this.state.isOnline) return;

    try {
      const startTime = Date.now();
      const response = await fetch('/api/health', {
        method: 'HEAD',
        cache: 'no-cache'
      });
      const endTime = Date.now();

      const latency = endTime - startTime;

      if (response.ok) {
        if (latency > 3000) {
          this.state.connectionType = 'slow';
        } else if (latency > 1000) {
          this.state.connectionType = 'unstable';
        } else {
          this.state.connectionType = 'online';
        }
      } else {
        this.state.connectionType = 'unstable';
      }

      this.notifyListeners();
    } catch (error) {
      // Connection failed, might be offline
      if (navigator.onLine) {
        this.state.connectionType = 'unstable';
      } else {
        this.handleOffline();
      }
    }
  }

  private async performSpeedTest(): Promise<void> {
    try {
      const startTime = Date.now();
      const response = await fetch('/api/health');
      const endTime = Date.now();

      if (response.ok) {
        const duration = (endTime - startTime) / 1000; // seconds
        const bytes = parseInt(response.headers.get('content-length') || '0');

        if (bytes > 0 && duration > 0) {
          const speed = (bytes * 8) / (duration * 1000000); // Mbps
          this.state.networkSpeed = speed;
          this.notifyListeners();
        }
      }
    } catch (error) {
      // Speed test failed, don't update speed
    }
  }

  private async processAction(action: QueuedAction): Promise<void> {
    switch (action.type) {
      case 'upload':
        return this.processUploadAction(action);
      case 'api_call':
        return this.processApiCallAction(action);
      case 'sync':
        return this.processSyncAction(action);
      default:
        throw new Error(`Unknown action type: ${action.type}`);
    }
  }

  private async processUploadAction(action: QueuedAction): Promise<void> {
    // Implement upload retry logic
    const { file, endpoint, options } = action.data;

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData,
      ...options
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
  }

  private async processApiCallAction(action: QueuedAction): Promise<void> {
    // Implement API call retry logic
    const { url, options } = action.data;

    const response = await fetch(url, options);

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`);
    }
  }

  private async processSyncAction(action: QueuedAction): Promise<void> {
    // Implement sync retry logic
    const { syncData } = action.data;

    // Process sync data
    console.log('Processing sync action:', syncData);
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.state);
      } catch (error) {
        console.error('Error in offline state listener:', error);
      }
    });
  }

  private generateActionId(): string {
    return `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getStorage(): OfflineStorage {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        return {
          queuedActions: parsed.queuedActions || [],
          cachedData: parsed.cachedData || {},
          userPreferences: parsed.userPreferences || {}
        };
      }
    } catch (error) {
      console.error('Error loading offline storage:', error);
    }

    return {
      queuedActions: [],
      cachedData: {},
      userPreferences: {}
    };
  }

  private saveStorage(storage: OfflineStorage): void {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(storage));
    } catch (error) {
      console.error('Error saving offline storage:', error);
    }
  }

  private loadFromStorage(): void {
    const storage = this.getStorage();
    this.actionQueue = storage.queuedActions.map(action => ({
      ...action,
      timestamp: new Date(action.timestamp)
    }));
  }

  private saveToStorage(): void {
    const storage = this.getStorage();
    storage.queuedActions = this.actionQueue;
    this.saveStorage(storage);
  }

  public destroy(): void {
    if (this.connectionCheckInterval) {
      clearInterval(this.connectionCheckInterval);
    }

    if (this.speedTestInterval) {
      clearInterval(this.speedTestInterval);
    }

    window.removeEventListener('online', this.handleOnline.bind(this));
    window.removeEventListener('offline', this.handleOffline.bind(this));

    if ('connection' in navigator) {
      (navigator as any).connection.removeEventListener('change', this.handleConnectionChange.bind(this));
    }
  }
}

// Export singleton instance
export const offlineManager = new OfflineManager();