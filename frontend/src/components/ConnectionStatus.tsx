import { useState, useEffect } from 'react';
import { healthMonitor, type HealthStatus } from '../lib/health-monitor';

interface ConnectionStatusProps {
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

export function ConnectionStatus({ 
  className = '', 
  showDetails = false, 
  compact = false 
}: ConnectionStatusProps) {
  const [status, setStatus] = useState<HealthStatus>(healthMonitor.getCurrentStatus());
  const [isRetrying, setIsRetrying] = useState(false);
  const [showDetailedInfo, setShowDetailedInfo] = useState(false);

  useEffect(() => {
    const unsubscribe = healthMonitor.onHealthChange((newStatus) => {
      setStatus(newStatus);
      setIsRetrying(false);
    });

    setStatus(healthMonitor.getCurrentStatus());

    return unsubscribe;
  }, []);

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await healthMonitor.forceHealthCheck();
    } catch (error) {
      console.error('Manual health check failed:', error);
    }
  };

  const handleToggleDetails = () => {
    setShowDetailedInfo(!showDetailedInfo);
    if (!showDetailedInfo) {
      healthMonitor.checkDetailedHealth();
    }
  };

  const getStatusColor = () => {
    if (isRetrying) return 'text-yellow-600';
    return status.isHealthy ? 'text-green-600' : 'text-red-600';
  };

  const getStatusBgColor = () => {
    if (isRetrying) return 'bg-yellow-100';
    return status.isHealthy ? 'bg-green-100' : 'bg-red-100';
  };

  const getStatusIcon = () => {
    if (isRetrying) {
      return (
        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      );
    }

    if (status.isHealthy) {
      return (
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      );
    }

    return (
      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
    );
  };

  const getStatusText = () => {
    if (isRetrying) return 'Checking...';
    if (status.isHealthy) return 'Connected';
    return status.error?.userMessage || 'Disconnected';
  };

  const formatResponseTime = (time: number) => {
    if (time < 1000) return `${Math.round(time)}ms`;
    return `${(time / 1000).toFixed(1)}s`;
  };

  if (compact) {
    return (
      <div className={`inline-flex items-center space-x-1 ${className}`}>
        <div className={`${getStatusColor()}`}>
          {getStatusIcon()}
        </div>
        {!status.isHealthy && (
          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
            title="Retry connection"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <div className={`inline-flex items-center space-x-2 px-3 py-2 rounded-md ${getStatusBgColor()}`}>
        <div className={`${getStatusColor()}`}>
          {getStatusIcon()}
        </div>
        <span className={`text-sm font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </span>
        
        {status.responseTime > 0 && (
          <span className="text-xs text-gray-500">
            ({formatResponseTime(status.responseTime)})
          </span>
        )}

        {!status.isHealthy && (
          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className="ml-2 px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            {isRetrying ? 'Checking...' : 'Retry'}
          </button>
        )}

        {showDetails && (
          <button
            onClick={handleToggleDetails}
            className="ml-2 px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            {showDetailedInfo ? 'Hide Details' : 'Details'}
          </button>
        )}
      </div>

      {showDetails && showDetailedInfo && (
        <div className="mt-2 p-3 bg-white border border-gray-200 rounded-md shadow-sm">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Last Check:</span>
              <span className="text-gray-900">
                {status.lastCheck.toLocaleTimeString()}
              </span>
            </div>
            
            {status.responseTime > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-600">Response Time:</span>
                <span className="text-gray-900">
                  {formatResponseTime(status.responseTime)}
                </span>
              </div>
            )}

            {status.error && (
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-600">Error Type:</span>
                  <span className="text-red-600">{status.error.type}</span>
                </div>
                <div className="text-gray-600">
                  <span>Message:</span>
                  <p className="text-red-600 text-xs mt-1">{status.error.technicalMessage}</p>
                </div>
              </div>
            )}

            {status.details && (
              <div className="space-y-1">
                <span className="text-gray-600">System Status:</span>
                <div className="text-xs bg-gray-50 p-2 rounded">
                  <pre className="whitespace-pre-wrap">
                    {JSON.stringify(status.details, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            <div className="pt-2 border-t border-gray-200">
              <div className="flex justify-between text-xs text-gray-500">
                <span>Health Monitor Stats:</span>
                <button
                  onClick={() => {
                    const stats = healthMonitor.getHealthStats();
                    console.log('Health Monitor Stats:', stats);
                  }}
                  className="text-blue-600 hover:text-blue-800"
                >
                  Log Stats
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function ConnectionIndicator({ className = '' }: { className?: string }) {
  return <ConnectionStatus compact className={className} />;
}

export function ConnectionStatusPanel({ className = '' }: { className?: string }) {
  return <ConnectionStatus showDetails className={className} />;
}