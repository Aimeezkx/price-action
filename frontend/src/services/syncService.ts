import { apiClient } from '../lib/api';

export interface SyncStatus {
  isOnline: boolean;
  lastSyncTime: Date | null;
  pendingChanges: number;
  syncInProgress: boolean;
  syncError: string | null;
  conflicts: number;
  dataConsistent: boolean;
}

export interface SyncConflict {
  id: string;
  entityType: string;
  field: string;
  clientValue: any;
  serverValue: any;
  resolution?: 'client_wins' | 'server_wins' | 'merge';
}

class SyncService {
  private clientId: string;
  private listeners: ((status: SyncStatus) => void)[] = [];
  private status: SyncStatus = {
    isOnline: navigator.onLine,
    lastSyncTime: null,
    pendingChanges: 0,
    syncInProgress: false,
    syncError: null,
    conflicts: 0,
    dataConsistent: true
  };

  constructor() {
    this.clientId = this.generateClientId();
    this.initializeNetworkListener();
    this.loadSyncStatus();
  }

  private generateClientId(): string {
    const stored = localStorage.getItem('sync_client_id');
    if (stored) return stored;
    
    const clientId = `web_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('sync_client_id', clientId);
    return clientId;
  }

  private initializeNetworkListener(): void {
    window.addEventListener('online', () => {
      this.status.isOnline = true;
      this.notifyListeners();
      this.performSync();
    });

    window.addEventListener('offline', () => {
      this.status.isOnline = false;
      this.notifyListeners();
    });
  }

  private async loadSyncStatus(): Promise<void> {
    try {
      const lastSyncStr = localStorage.getItem('last_sync_time');
      if (lastSyncStr) {
        this.status.lastSyncTime = new Date(lastSyncStr);
      }
    } catch (error) {
      console.error('Failed to load sync status:', error);
    }
  }

  public addSyncListener(listener: (status: SyncStatus) => void): () => void {
    this.listeners.push(listener);
    listener(this.status);
    
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.status);
      } catch (error) {
        console.error('Sync listener error:', error);
      }
    });
  }

  public async performSync(): Promise<void> {
    if (!this.status.isOnline || this.status.syncInProgress) {
      return;
    }

    this.status.syncInProgress = true;
    this.status.syncError = null;
    this.notifyListeners();

    try {
      // For web platform, sync is primarily server-to-client
      // since the web app doesn't have extensive offline capabilities
      
      // Check sync status with server
      const serverStatus = await this.checkServerSyncStatus();
      
      // Validate data consistency if needed
      if (!serverStatus.dataConsistent) {
        await this.performFullSync();
      }

      this.status.lastSyncTime = new Date();
      this.status.dataConsistent = true;
      localStorage.setItem('last_sync_time', this.status.lastSyncTime.toISOString());

    } catch (error) {
      this.status.syncError = error instanceof Error ? error.message : 'Sync failed';
      console.error('Sync failed:', error);
    } finally {
      this.status.syncInProgress = false;
      this.notifyListeners();
    }
  }

  private async checkServerSyncStatus(): Promise<any> {
    const response = await fetch(`${apiClient.baseUrl}/sync/status?client_id=${this.clientId}`);
    if (!response.ok) {
      throw new Error(`Sync status check failed: ${response.status}`);
    }
    return response.json();
  }

  private async performFullSync(): Promise<void> {
    const response = await fetch(`${apiClient.baseUrl}/sync/full-sync?client_id=${this.clientId}&platform=web&force=true`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})
    });

    if (!response.ok) {
      throw new Error(`Full sync failed: ${response.status}`);
    }

    // In a real implementation, this would update local caches
    // For now, we'll just mark as consistent
    this.status.dataConsistent = true;
  }

  public getSyncStatus(): SyncStatus {
    return { ...this.status };
  }

  public async forceSync(): Promise<void> {
    return this.performSync();
  }

  public getConflicts(): SyncConflict[] {
    // Web platform conflicts would be handled differently
    // For now, return empty array
    return [];
  }

  public async resolveConflict(conflictId: string, resolution: 'client_wins' | 'server_wins' | 'merge'): Promise<void> {
    // Implementation would depend on specific conflict resolution needs
    console.log(`Resolving conflict ${conflictId} with ${resolution}`);
  }
}

export const syncService = new SyncService();