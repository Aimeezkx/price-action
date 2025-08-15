import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertCircle, RefreshCw, Wifi, WifiOff, Clock } from 'lucide-react';

interface SyncStatus {
  isOnline: boolean;
  lastSyncTime: Date | null;
  pendingChanges: number;
  syncInProgress: boolean;
  syncError: string | null;
  conflicts: number;
  dataConsistent: boolean;
}

interface SyncStatusIndicatorProps {
  onForceSync?: () => void;
  onResolveConflicts?: () => void;
}

export const SyncStatusIndicator: React.FC<SyncStatusIndicatorProps> = ({
  onForceSync,
  onResolveConflicts
}) => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    isOnline: navigator.onLine,
    lastSyncTime: null,
    pendingChanges: 0,
    syncInProgress: false,
    syncError: null,
    conflicts: 0,
    dataConsistent: true
  });

  useEffect(() => {
    // Listen for online/offline events
    const handleOnline = () => setSyncStatus(prev => ({ ...prev, isOnline: true }));
    const handleOffline = () => setSyncStatus(prev => ({ ...prev, isOnline: false }));

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Simulate sync status updates (in real app, this would come from sync service)
    const interval = setInterval(() => {
      // This would be replaced with actual sync service status
      setSyncStatus(prev => ({
        ...prev,
        lastSyncTime: new Date(),
        pendingChanges: Math.max(0, prev.pendingChanges - 1)
      }));
    }, 30000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  const getStatusIcon = () => {
    if (!syncStatus.isOnline) {
      return <WifiOff className="w-4 h-4 text-gray-400" />;
    }
    
    if (syncStatus.syncInProgress) {
      return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
    }
    
    if (syncStatus.syncError || syncStatus.conflicts > 0 || !syncStatus.dataConsistent) {
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
    
    if (syncStatus.pendingChanges > 0) {
      return <Clock className="w-4 h-4 text-yellow-500" />;
    }
    
    return <CheckCircle className="w-4 h-4 text-green-500" />;
  };

  const getStatusText = () => {
    if (!syncStatus.isOnline) return 'Offline';
    if (syncStatus.syncInProgress) return 'Syncing...';
    if (syncStatus.syncError) return 'Sync Error';
    if (syncStatus.conflicts > 0) return `${syncStatus.conflicts} Conflicts`;
    if (!syncStatus.dataConsistent) return 'Data Inconsistent';
    if (syncStatus.pendingChanges > 0) return `${syncStatus.pendingChanges} Pending`;
    return 'Synced';
  };

  return (
    <div className="flex items-center space-x-2 text-sm">
      <div className="flex items-center space-x-1">
        {getStatusIcon()}
        <span className="text-gray-600">{getStatusText()}</span>
      </div>
      
      {syncStatus.lastSyncTime && (
        <span className="text-xs text-gray-400">
          {syncStatus.lastSyncTime.toLocaleTimeString()}
        </span>
      )}
      
      {(syncStatus.syncError || syncStatus.conflicts > 0) && (
        <div className="flex space-x-1">
          {onForceSync && (
            <button
              onClick={onForceSync}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Retry
            </button>
          )}
          {syncStatus.conflicts > 0 && onResolveConflicts && (
            <button
              onClick={onResolveConflicts}
              className="text-xs text-orange-600 hover:text-orange-800"
            >
              Resolve
            </button>
          )}
        </div>
      )}
    </div>
  );
};