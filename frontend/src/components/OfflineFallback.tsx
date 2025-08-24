/**
 * Offline Fallback Component
 * Provides fallback UI states when API is unavailable
 * Shows cached data and offline-capable features
 */

import React from 'react';
import { useOfflineMode } from '../hooks/useOfflineMode';

export interface OfflineFallbackProps {
  children: React.ReactNode;
  fallbackContent?: React.ReactNode;
  showCachedData?: boolean;
  cachedDataKey?: string;
  className?: string;
}

export const OfflineFallback: React.FC<OfflineFallbackProps> = ({
  children,
  fallbackContent,
  showCachedData = true,
  cachedDataKey,
  className = ''
}) => {
  const { isOnline, getCachedData } = useOfflineMode();

  // If online, show normal content
  if (isOnline) {
    return <>{children}</>;
  }

  // If offline, show fallback content or cached data
  const cachedData = cachedDataKey ? getCachedData(cachedDataKey) : null;

  return (
    <div className={`offline-fallback ${className}`}>
      {fallbackContent ? (
        fallbackContent
      ) : (
        <div className="text-center py-8">
          <div className="max-w-md mx-auto">
            <div className="mb-4">
              <span className="text-6xl" role="img" aria-label="Offline">
                📡
              </span>
            </div>
            
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              You're currently offline
            </h3>
            
            <p className="text-sm text-gray-600 mb-4">
              Some features may be limited while you're offline. 
              We'll sync your changes when you're back online.
            </p>

            {showCachedData && cachedData && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-blue-900 mb-2">
                  📋 Showing cached data
                </h4>
                <p className="text-xs text-blue-700">
                  This information was last updated when you were online.
                  It may not reflect the most recent changes.
                </p>
              </div>
            )}

            <div className="space-y-2 text-xs text-gray-500">
              <p>✓ You can still browse previously loaded content</p>
              <p>✓ Your changes will be saved locally</p>
              <p>✓ Everything will sync when you're back online</p>
            </div>
          </div>
        </div>
      )}

      {/* Show cached data if available */}
      {showCachedData && cachedData && (
        <div className="mt-6 border-t pt-6">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
            <div className="flex items-center">
              <span className="text-yellow-600 mr-2">⚠️</span>
              <span className="text-sm text-yellow-800">
                Showing cached content from when you were last online
              </span>
            </div>
          </div>
          
          {/* Render cached data */}
          <div className="opacity-75">
            {typeof cachedData === 'object' ? (
              <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto">
                {JSON.stringify(cachedData, null, 2)}
              </pre>
            ) : (
              <div>{cachedData}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Specialized fallback components for different scenarios

export const DocumentListFallback: React.FC<{ cachedDocuments?: any[] }> = ({ 
  cachedDocuments = [] 
}) => {
  return (
    <div className="space-y-4">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center">
          <span className="text-yellow-600 mr-2">📡</span>
          <div>
            <h3 className="text-sm font-medium text-yellow-800">
              Offline Mode
            </h3>
            <p className="text-xs text-yellow-700 mt-1">
              Showing {cachedDocuments.length} cached documents. 
              New uploads will be queued until you're back online.
            </p>
          </div>
        </div>
      </div>

      {cachedDocuments.length > 0 ? (
        <div className="space-y-2">
          {cachedDocuments.map((doc, index) => (
            <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-3 opacity-75">
              <h4 className="font-medium text-gray-900">{doc.title || `Document ${index + 1}`}</h4>
              <p className="text-sm text-gray-600 mt-1">
                {doc.description || 'No description available'}
              </p>
              <div className="flex items-center mt-2 text-xs text-gray-500">
                <span>📄 Cached</span>
                {doc.lastModified && (
                  <span className="ml-2">
                    Last modified: {new Date(doc.lastModified).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>No cached documents available</p>
          <p className="text-xs mt-1">Documents will appear here once you're back online</p>
        </div>
      )}
    </div>
  );
};

export const UploadFallback: React.FC = () => {
  const { queueStats } = useOfflineMode();

  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center bg-gray-50">
      <div className="space-y-4">
        <span className="text-4xl" role="img" aria-label="Offline upload">
          📤
        </span>
        
        <div>
          <h3 className="text-lg font-medium text-gray-900">
            Offline Upload Mode
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            You can still select files to upload. They'll be queued and uploaded 
            automatically when your connection is restored.
          </p>
        </div>

        {queueStats.total > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              📋 {queueStats.total} file{queueStats.total !== 1 ? 's' : ''} queued for upload
            </p>
          </div>
        )}

        <button
          type="button"
          className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Queue Files for Upload
        </button>
      </div>
    </div>
  );
};

export const SearchFallback: React.FC<{ cachedResults?: any[] }> = ({ 
  cachedResults = [] 
}) => {
  return (
    <div className="space-y-4">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center">
          <span className="text-yellow-600 mr-2">🔍</span>
          <div>
            <h3 className="text-sm font-medium text-yellow-800">
              Offline Search
            </h3>
            <p className="text-xs text-yellow-700 mt-1">
              Search is limited to cached content while offline.
              Full search will be available when you're back online.
            </p>
          </div>
        </div>
      </div>

      {cachedResults.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-900">
            Cached Search Results
          </h4>
          {cachedResults.map((result, index) => (
            <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-3 opacity-75">
              <h5 className="font-medium text-gray-900">{result.title}</h5>
              <p className="text-sm text-gray-600 mt-1">{result.excerpt}</p>
              <span className="text-xs text-gray-500">📄 Cached result</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>No cached search results available</p>
          <p className="text-xs mt-1">Try searching when you're back online</p>
        </div>
      )}
    </div>
  );
};

export default OfflineFallback;