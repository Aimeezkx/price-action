/**
 * Offline Indicator Component
 * Displays connection status and offline mode information
 * Provides user feedback about network connectivity
 */

import React, { useState } from 'react';
import { useOfflineMode } from '../hooks/useOfflineMode';

export interface OfflineIndicatorProps {
  position?: 'top' | 'bottom';
  showDetails?: boolean;
  className?: string;
}

export const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({
  position = 'top',
  showDetails = false,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { 
    isOnline, 
    isOffline, 
    connectionQuality, 
    state, 
    queueStats, 
    processQueue 
  } = useOfflineMode();

  const getStatusColor = () => {
    if (isOffline) return 'bg-red-500';
    if (connectionQuality === 'poor') return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getStatusText = () => {
    if (isOffline) return 'Offline';
    if (connectionQuality === 'poor') return 'Poor Connection';
    return 'Online';
  };

  const getStatusIcon = () => {
    if (isOffline) return '📡';
    if (connectionQuality === 'poor') return '⚠️';
    return '✅';
  };

  const formatLastOnline = (date: Date | null) => {
    if (!date) return 'Unknown';
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
  };

  const handleRetryConnection = async () => {
    if (isOnline && queueStats.total > 0) {
      try {
        await processQueue();
      } catch (error) {
        console.error('Failed to process queue:', error);
      }
    }
  };

  const positionClasses = position === 'top' 
    ? 'top-0 left-0 right-0' 
    : 'bottom-0 left-0 right-0';

  // Don't show indicator if online and no queued actions
  if (isOnline && queueStats.total === 0 && !showDetails) {
    return null;
  }

  return (
    <div className={`fixed ${positionClasses} z-40 ${className}`}>
      <div className={`${getStatusColor()} text-white shadow-lg`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-2">
            <div className="flex items-center space-x-3">
              <span className="text-lg" role="img" aria-label="Connection status">
                {getStatusIcon()}
              </span>
              
              <div className="flex items-center space-x-2">
                <span className="font-medium text-sm">
                  {getStatusText()}
                </span>
                
                {queueStats.total > 0 && (
                  <span className="bg-white bg-opacity-20 px-2 py-1 rounded-full text-xs">
                    {queueStats.total} queued
                  </span>
                )}
                
                {state.networkSpeed && (
                  <span className="text-xs opacity-75">
                    {state.networkSpeed.toFixed(1)} Mbps
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {isOnline && queueStats.total > 0 && (
                <button
                  onClick={handleRetryConnection}
                  className="bg-white bg-opacity-20 hover:bg-opacity-30 px-3 py-1 rounded text-xs font-medium transition-colors"
                >
                  Process Queue
                </button>
              )}
              
              {showDetails && (
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="bg-white bg-opacity-20 hover:bg-opacity-30 px-2 py-1 rounded text-xs transition-colors"
                >
                  {isExpanded ? '▲' : '▼'}
                </button>
              )}
            </div>
          </div>

          {/* Expanded Details */}
          {isExpanded && showDetails && (
            <div className="pb-3 border-t border-white border-opacity-20 pt-3">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div>
                  <h4 className="font-medium mb-1">Connection Info</h4>
                  <p>Status: {state.connectionType}</p>
                  {state.networkSpeed && (
                    <p>Speed: {state.networkSpeed.toFixed(1)} Mbps</p>
                  )}
                  {isOffline && state.lastOnlineTime && (
                    <p>Last online: {formatLastOnline(state.lastOnlineTime)}</p>
                  )}
                </div>

                {queueStats.total > 0 && (
                  <div>
                    <h4 className="font-medium mb-1">Queued Actions</h4>
                    <p>Total: {queueStats.total}</p>
                    {Object.entries(queueStats.byType).map(([type, count]) => (
                      <p key={type}>{type}: {count}</p>
                    ))}
                  </div>
                )}

                <div>
                  <h4 className="font-medium mb-1">Actions</h4>
                  {isOffline && (
                    <p className="text-white text-opacity-75">
                      Working offline. Changes will sync when connection is restored.
                    </p>
                  )}
                  {connectionQuality === 'poor' && (
                    <p className="text-white text-opacity-75">
                      Slow connection detected. Some features may be limited.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OfflineIndicator;