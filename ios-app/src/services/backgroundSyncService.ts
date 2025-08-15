import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { AppState, AppStateStatus } from 'react-native';
import { apiClient } from './api';
import { offlineStorage } from './offlineStorage';
import { generateClientId } from '../utils/deviceUtils';

export interface SyncStatus {
  isOnline: boolean;
  lastSyncTime: Date | null;
  pendingChanges: number;
  syncInProgress: boolean;
  syncError: string | null;
  conflicts: number;
  dataConsistent: boolean;
}

export interface SyncResult {
  success: boolean;
  syncedItems: number;
  conflicts: number;
  error?: string;
  conflictDetails?: any[];
}

export interface SyncConflict {
  id: string;
  entityType: string;
  field: string;
  clientValue: any;
  serverValue: any;
  resolution?: 'client_wins' | 'server_wins' | 'merge';
}

class BackgroundSyncService {
  private readonly SYNC_INTERVAL = 5 * 60 * 1000; // 5 minutes
  private readonly RETRY_DELAY = 30 * 1000; // 30 seconds
  private readonly MAX_RETRIES = 3;
  private readonly SYNC_STATUS_KEY = 'background_sync_status';

  private syncTimer: any = null;
  private retryTimer: any = null;
  private isOnline = false;
  private syncInProgress = false;
  private appState: AppStateStatus = 'active';
  private listeners: ((status: SyncStatus) => void)[] = [];
  private lastSyncTime: Date | null = null;
  private pendingChanges: any[] = [];
  private syncError: string | null = null;
  private conflicts: SyncConflict[] = [];
  private clientId: string = '';
  private dataConsistent = true;

  constructor() {
    this.initializeSync();
  }

  private async initializeSync() {
    // Generate or load client ID
    this.clientId = await this.getOrCreateClientId();

    // Load last sync time
    try {
      const lastSync = await AsyncStorage.getItem('last_sync_time');
      if (lastSync) {
        this.lastSyncTime = new Date(lastSync);
      }
    } catch (error) {
      console.error('Failed to load last sync time:', error);
    }

    this.initializeNetworkListener();
    this.initializeAppStateListener();

    // Load pending changes
    await this.loadPendingChanges();

    // Perform initial consistency check
    await this.validateDataConsistency();
  }

  private async getOrCreateClientId(): Promise<string> {
    try {
      let clientId = await AsyncStorage.getItem('sync_client_id');
      if (!clientId) {
        clientId = await generateClientId();
        await AsyncStorage.setItem('sync_client_id', clientId);
      }
      return clientId;
    } catch (error) {
      console.error('Failed to get/create client ID:', error);
      return `ios_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
  }

  private async loadPendingChanges() {
    try {
      this.pendingChanges = await offlineStorage.getPendingChanges();
      this.notifyListeners();
    } catch (error) {
      console.error('Failed to load pending changes:', error);
    }
  }

  private initializeNetworkListener(): void {
    NetInfo.addEventListener(state => {
      const wasOnline = this.isOnline;
      this.isOnline = state.isConnected ?? false;

      if (!wasOnline && this.isOnline) {
        // Just came online, trigger sync
        this.triggerSync();
      }

      this.notifyListeners();
    });

    // Get initial network state
    NetInfo.fetch().then(state => {
      this.isOnline = state.isConnected ?? false;
      this.notifyListeners();
    });
  }

  private initializeAppStateListener(): void {
    AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      const wasBackground = this.appState === 'background';
      this.appState = nextAppState;

      if (wasBackground && nextAppState === 'active') {
        // App came to foreground, trigger sync
        this.triggerSync();
      }

      if (nextAppState === 'background') {
        // App went to background, stop regular sync
        this.stopRegularSync();
      } else if (nextAppState === 'active') {
        // App became active, start regular sync
        this.startRegularSync();
      }
    });
  }

  async startBackgroundSync(): Promise<void> {
    console.log('Starting background sync service');
    
    // Load initial sync status
    await this.loadSyncStatus();
    
    // Start regular sync if app is active
    if (this.appState === 'active') {
      this.startRegularSync();
    }

    // Trigger initial sync if online
    if (this.isOnline) {
      this.triggerSync();
    }
  }

  stopBackgroundSync(): void {
    console.log('Stopping background sync service');
    this.stopRegularSync();
    this.clearRetryTimer();
  }

  private startRegularSync(): void {
    if (this.syncTimer) return;

    this.syncTimer = setInterval(() => {
      if (this.isOnline && !this.syncInProgress) {
        this.triggerSync();
      }
    }, this.SYNC_INTERVAL);
  }

  private stopRegularSync(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
  }

  private clearRetryTimer(): void {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
  }

  async triggerSync(): Promise<SyncResult> {
    if (!this.isOnline || this.syncInProgress) {
      return {
        success: false,
        syncedChanges: 0,
        errors: ['Sync already in progress or offline'],
        timestamp: new Date(),
      };
    }

    this.syncInProgress = true;
    this.notifyListeners();

    try {
      const result = await this.performSync();
      
      if (result.success) {
        await this.updateLastSyncTime();
        this.clearRetryTimer();
      } else {
        this.scheduleRetry();
      }

      return result;
    } catch (error) {
      console.error('Sync failed:', error);
      this.scheduleRetry();
      
      return {
        success: false,
        syncedChanges: 0,
        errors: [error instanceof Error ? error.message : 'Unknown sync error'],
        timestamp: new Date(),
      };
    } finally {
      this.syncInProgress = false;
      this.notifyListeners();
    }
  }

  private async performSync(): Promise<SyncResult> {
    try {
      // Step 1: Push local changes to server
      const pushResult = await this.pushLocalChanges();
      
      // Step 2: Pull server changes
      const pullResult = await this.pullServerChanges();
      
      // Step 3: Validate data consistency
      await this.validateDataConsistency();
      
      // Step 4: Update sync metadata
      this.lastSyncTime = new Date();
      await AsyncStorage.setItem('last_sync_time', this.lastSyncTime.toISOString());
      await offlineStorage.setLastSyncTime(this.lastSyncTime);
      
      // Clear pending changes if push was successful
      if (pushResult.success) {
        await offlineStorage.clearPendingChanges();
        this.pendingChanges = [];
      }

      const result: SyncResult = {
        success: pushResult.success && pullResult.success,
        syncedItems: pushResult.syncedItems + pullResult.syncedItems,
        conflicts: pushResult.conflicts + pullResult.conflicts,
        conflictDetails: [...(pushResult.conflictDetails || []), ...(pullResult.conflictDetails || [])]
      };

      if (!result.success) {
        result.error = pushResult.error || pullResult.error;
        this.syncError = result.error || null;
      }

      return result;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown sync error';
      this.syncError = errorMessage;
      
      return {
        success: false,
        syncedItems: 0,
        conflicts: 0,
        error: errorMessage,
      };
    }
  }

  private async pushLocalChanges(): Promise<SyncResult> {
    try {
      const pendingChanges = await offlineStorage.getPendingChanges();
      
      if (pendingChanges.length === 0) {
        return { success: true, syncedItems: 0, conflicts: 0 };
      }

      // Convert pending changes to sync format
      const syncChanges = pendingChanges.map(change => ({
        id: change.data.cardId || change.data.id || change.id,
        entity_type: this.mapChangeTypeToEntity(change.type),
        operation: this.mapChangeTypeToOperation(change.type),
        data: change.data,
        timestamp: change.timestamp,
        client_id: this.clientId,
        version: 1
      }));

      // Push changes to server
      const response = await this.callSyncAPI('/sync/push', {
        last_sync_time: this.lastSyncTime?.toISOString(),
        client_id: this.clientId,
        platform: 'ios',
        changes: syncChanges
      });

      // Handle conflicts
      if (response.conflicts && response.conflicts.length > 0) {
        this.conflicts = response.conflicts.map(this.mapServerConflictToLocal);
        // Auto-resolve simple conflicts (server wins for now)
        await this.resolveConflicts(this.conflicts);
      }

      return {
        success: response.success,
        syncedItems: response.stats?.pushed_changes || 0,
        conflicts: response.conflicts?.length || 0,
        conflictDetails: response.conflicts
      };

    } catch (error) {
      return {
        success: false,
        syncedItems: 0,
        conflicts: 0,
        error: error instanceof Error ? error.message : 'Failed to push changes',
      };
    }
  }

  private async pullServerChanges(): Promise<SyncResult> {
    try {
      // Pull changes from server
      const response = await this.callSyncAPI('/sync/pull', {
        last_sync_time: this.lastSyncTime?.toISOString(),
        client_id: this.clientId,
        platform: 'ios',
        changes: []
      });

      if (!response.success) {
        throw new Error('Server pull failed');
      }

      // Apply server changes to local storage
      let syncedItems = 0;
      for (const change of response.changes || []) {
        await this.applyServerChange(change);
        syncedItems++;
      }

      return {
        success: true,
        syncedItems,
        conflicts: 0
      };

    } catch (error) {
      return {
        success: false,
        syncedItems: 0,
        conflicts: 0,
        error: error instanceof Error ? error.message : 'Failed to pull server changes',
      };
    }
  }

  private async applyServerChange(change: any): Promise<void> {
    switch (change.entity_type) {
      case 'document':
        if (change.operation === 'create' || change.operation === 'update') {
          await offlineStorage.saveDocument(change.data);
        }
        break;
      
      case 'chapter':
        if (change.operation === 'create' || change.operation === 'update') {
          const chapters = await offlineStorage.getChapters();
          const updatedChapters = chapters.filter(c => c.id !== change.data.id);
          updatedChapters.push(change.data);
          await offlineStorage.saveChapters(updatedChapters);
        }
        break;
      
      case 'card':
        if (change.operation === 'create' || change.operation === 'update') {
          const cards = await offlineStorage.getCards();
          const updatedCards = cards.filter(c => c.id !== change.data.id);
          updatedCards.push(change.data);
          await offlineStorage.saveCards(updatedCards);
        }
        break;
      
      case 'srs':
        if (change.operation === 'create' || change.operation === 'update') {
          const srsStates = await offlineStorage.getSRSStates();
          const updatedStates = srsStates.filter(s => s.cardId !== change.data.cardId);
          updatedStates.push({
            id: change.data.id,
            cardId: change.data.card_id,
            easeFactor: change.data.ease_factor,
            interval: change.data.interval,
            repetitions: change.data.repetitions,
            dueDate: change.data.due_date,
            lastReviewed: change.data.last_reviewed
          });
          await offlineStorage.saveSRSStates(updatedStates);
        }
        break;
    }
  }

  private async validateDataConsistency(): Promise<void> {
    try {
      // Calculate checksums for local data
      const documents = await offlineStorage.getDocuments();
      const cards = await offlineStorage.getCards();
      const srsStates = await offlineStorage.getSRSStates();

      const checksums = {
        document: this.calculateChecksum(documents),
        card: this.calculateChecksum(cards),
        srs: this.calculateChecksum(srsStates)
      };

      // Validate with server
      const response = await this.callSyncAPI('/sync/validate-consistency', {
        client_id: this.clientId,
        entity_checksums: checksums
      });

      this.dataConsistent = response.overall_consistent;

      if (!this.dataConsistent && response.recommendation === 'full_sync') {
        // Trigger full sync if data is inconsistent
        await this.performFullSync();
      }

    } catch (error) {
      console.warn('Failed to validate data consistency:', error);
      this.dataConsistent = false;
    }
  }

  private calculateChecksum(data: any[]): string {
    const sortedData = data
      .map(item => {
        const cleanItem = { ...item };
        delete cleanItem.created_at;
        delete cleanItem.updated_at;
        return cleanItem;
      })
      .sort((a, b) => (a.id || '').localeCompare(b.id || ''));
    
    return btoa(JSON.stringify(sortedData)).slice(0, 32);
  }

  private async performFullSync(): Promise<SyncResult> {
    try {
      const response = await this.callSyncAPI('/sync/full-sync', {
        client_id: this.clientId,
        platform: 'ios',
        force: true
      });

      if (response.success) {
        // Clear all local data and apply server data
        await offlineStorage.clearAllOfflineData();
        
        for (const change of response.changes || []) {
          await this.applyServerChange(change);
        }

        this.dataConsistent = true;
        this.lastSyncTime = new Date();
        await AsyncStorage.setItem('last_sync_time', this.lastSyncTime.toISOString());
      }

      return {
        success: response.success,
        syncedItems: response.stats?.total_changes || 0,
        conflicts: 0
      };

    } catch (error) {
      return {
        success: false,
        syncedItems: 0,
        conflicts: 0,
        error: error instanceof Error ? error.message : 'Full sync failed'
      };
    }
  }

  private async resolveConflicts(conflicts: SyncConflict[]): Promise<void> {
    const resolutions = conflicts.map(conflict => ({
      conflict_id: conflict.id,
      resolution: 'server_wins', // Default resolution
      merged_data: null
    }));

    try {
      await this.callSyncAPI('/sync/resolve-conflicts', resolutions, {
        client_id: this.clientId
      });
      
      // Clear resolved conflicts
      this.conflicts = [];
    } catch (error) {
      console.error('Failed to resolve conflicts:', error);
    }
  }

  private async callSyncAPI(endpoint: string, data: any, params?: any): Promise<any> {
    const baseUrl = 'http://localhost:8000/api'; // Should match your backend
    const url = `${baseUrl}${endpoint}`;
    const queryParams = params ? `?${new URLSearchParams(params)}` : '';
    
    const response = await fetch(`${url}${queryParams}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`Sync API error: ${response.status}`);
    }

    return response.json();
  }

  private mapChangeTypeToEntity(changeType: string): string {
    const mapping: Record<string, string> = {
      'srs_update': 'srs',
      'study_session': 'study_session',
      'card_create': 'card',
      'card_update': 'card',
      'document_create': 'document',
      'document_update': 'document'
    };
    return mapping[changeType] || 'unknown';
  }

  private mapChangeTypeToOperation(changeType: string): string {
    if (changeType.includes('create')) return 'create';
    if (changeType.includes('update')) return 'update';
    if (changeType.includes('delete')) return 'delete';
    return 'update';
  }

  private mapServerConflictToLocal(serverConflict: any): SyncConflict {
    return {
      id: serverConflict.conflict_id,
      entityType: serverConflict.entity_type,
      field: serverConflict.conflicts[0]?.field || 'unknown',
      clientValue: serverConflict.conflicts[0]?.client_value,
      serverValue: serverConflict.conflicts[0]?.server_value
    };
  }



  private scheduleRetry(): void {
    this.clearRetryTimer();
    
    this.retryTimer = setTimeout(() => {
      if (this.isOnline && !this.syncInProgress) {
        this.triggerSync();
      }
    }, this.RETRY_DELAY);
  }

  private async loadSyncStatus(): Promise<void> {
    try {
      const statusJson = await AsyncStorage.getItem(this.SYNC_STATUS_KEY);
      if (statusJson) {
        const status = JSON.parse(statusJson);
        // Load any persisted sync status if needed
      }
    } catch (error) {
      console.error('Failed to load sync status:', error);
    }
  }

  private async updateLastSyncTime(): Promise<void> {
    try {
      await offlineStorage.setLastSyncTime(new Date());
      await this.saveSyncStatus();
    } catch (error) {
      console.error('Failed to update last sync time:', error);
    }
  }

  private async saveSyncStatus(): Promise<void> {
    try {
      const status = await this.getSyncStatus();
      await AsyncStorage.setItem(this.SYNC_STATUS_KEY, JSON.stringify(status));
    } catch (error) {
      console.error('Failed to save sync status:', error);
    }
  }

  async getSyncStatus(): Promise<SyncStatus> {
    return {
      isOnline: this.isOnline,
      lastSyncTime: this.lastSyncTime,
      pendingChanges: this.pendingChanges.length,
      syncInProgress: this.syncInProgress,
      syncError: this.syncError,
      conflicts: this.conflicts.length,
      dataConsistent: this.dataConsistent,
    };
  }

  addSyncStatusListener(listener: (status: SyncStatus) => void): () => void {
    this.listeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private async notifyListeners(): Promise<void> {
    if (this.listeners.length === 0) return;

    try {
      const status = await this.getSyncStatus();
      this.listeners.forEach(listener => {
        try {
          listener(status);
        } catch (error) {
          console.error('Sync status listener error:', error);
        }
      });
    } catch (error) {
      console.error('Failed to notify sync status listeners:', error);
    }
  }

  // Manual sync trigger for user-initiated sync
  async forcSync(): Promise<SyncResult> {
    console.log('Force sync triggered by user');
    return this.triggerSync();
  }

  public getConflicts(): SyncConflict[] {
    return this.conflicts;
  }

  public async resolveConflict(conflictId: string, resolution: 'client_wins' | 'server_wins' | 'merge'): Promise<void> {
    const conflict = this.conflicts.find(c => c.id === conflictId);
    if (conflict) {
      conflict.resolution = resolution;
      await this.resolveConflicts([conflict]);
    }
  }

  public async clearSyncData(): Promise<void> {
    try {
      await AsyncStorage.removeItem('last_sync_time');
      await offlineStorage.clearPendingChanges();
      this.lastSyncTime = null;
      this.pendingChanges = [];
      this.syncError = null;
      this.conflicts = [];
      this.dataConsistent = true;
      this.notifyListeners();
    } catch (error) {
      console.error('Failed to clear sync data:', error);
    }
  }

  public async exportSyncData(): Promise<any> {
    return {
      clientId: this.clientId,
      lastSyncTime: this.lastSyncTime?.toISOString(),
      pendingChanges: this.pendingChanges,
      conflicts: this.conflicts,
      dataConsistent: this.dataConsistent,
      offlineData: await offlineStorage.exportOfflineData(),
    };
  }

  public async importSyncData(data: any): Promise<void> {
    try {
      if (data.clientId) {
        this.clientId = data.clientId;
        await AsyncStorage.setItem('sync_client_id', this.clientId);
      }

      if (data.lastSyncTime) {
        this.lastSyncTime = new Date(data.lastSyncTime);
        await AsyncStorage.setItem('last_sync_time', this.lastSyncTime.toISOString());
      }

      if (data.offlineData) {
        await offlineStorage.importOfflineData(data.offlineData);
      }

      if (data.pendingChanges) {
        this.pendingChanges = data.pendingChanges;
      }

      if (data.conflicts) {
        this.conflicts = data.conflicts;
      }

      this.dataConsistent = data.dataConsistent ?? true;

      this.notifyListeners();
    } catch (error) {
      console.error('Failed to import sync data:', error);
      throw error;
    }
  }

  // Get sync statistics
  async getSyncStats(): Promise<{
    totalSyncs: number;
    lastSyncDuration: number;
    averageSyncDuration: number;
    failedSyncs: number;
  }> {
    // This would require additional tracking of sync statistics
    // For now, return basic stats
    return {
      totalSyncs: 0,
      lastSyncDuration: 0,
      averageSyncDuration: 0,
      failedSyncs: 0,
    };
  }
}

export const backgroundSyncService = new BackgroundSyncService();