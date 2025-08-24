import React, { useState, useEffect } from 'react';
import { DebugConsole } from './DebugConsole';
import { ApiPerformanceDashboard } from './ApiPerformanceDashboard';
import { apiLogger, LogLevel } from '../lib/api-logger';
import { healthMonitor } from '../lib/health-monitor';
import { apiPerformanceMonitor } from '../lib/api-performance-monitor';
import { configManager } from '../lib/config';

interface DebugToolbarProps {
  enabled?: boolean;
}

export const DebugToolbar: React.FC<DebugToolbarProps> = ({ enabled = true }) => {
  const [isConsoleOpen, setIsConsoleOpen] = useState(false);
  const [isDashboardOpen, setIsDashboardOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [errorCount, setErrorCount] = useState(0);
  const [isHealthy, setIsHealthy] = useState(false);
  const [responseTime, setResponseTime] = useState(0);
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    if (!enabled) return;

    // Subscribe to new log entries to update error count
    const unsubscribeLogger = apiLogger.subscribe((entry) => {
      if (entry.level === LogLevel.ERROR) {
        setErrorCount(prev => prev + 1);
      }
    });

    // Subscribe to health status changes
    const unsubscribeHealth = healthMonitor.onHealthChange((status) => {
      setIsHealthy(status.isHealthy);
      setResponseTime(status.responseTime);
    });

    // Initial health status
    const currentHealth = healthMonitor.getCurrentStatus();
    setIsHealthy(currentHealth.isHealthy);
    setResponseTime(currentHealth.responseTime);

    // Subscribe to performance alerts
    const unsubscribeAlerts = apiPerformanceMonitor.onAlert(() => {
      setAlertCount(prev => prev + 1);
    });

    // Initial error count
    const stats = apiLogger.getStats();
    setErrorCount(stats.byLevel[LogLevel.ERROR]);

    // Initial alert count
    const currentAlerts = apiPerformanceMonitor.getAlerts();
    setAlertCount(currentAlerts.length);

    return () => {
      unsubscribeLogger();
      unsubscribeHealth();
      unsubscribeAlerts();
    };
  }, [enabled]);

  const handleExportLogs = () => {
    const logsJson = apiLogger.exportLogs();
    const blob = new Blob([logsJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debug-logs-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleClearLogs = () => {
    apiLogger.clearLogs();
    setErrorCount(0);
  };

  const handleForceHealthCheck = async () => {
    await healthMonitor.forceHealthCheck();
  };

  const getHealthStatusColor = () => {
    if (isHealthy) return 'bg-green-500';
    return 'bg-red-500';
  };

  const getHealthStatusText = () => {
    if (isHealthy) return `Healthy (${responseTime}ms)`;
    return 'Unhealthy';
  };

  // Force enable in development for testing
  const shouldShow = enabled || import.meta.env.DEV || process.env.NODE_ENV === 'development';
  
  if (!shouldShow) {
    return null;
  }

  return (
    <>
      <div className="fixed bottom-4 right-4 z-40">
        <div className={`bg-gray-800 text-white rounded-lg shadow-lg transition-all duration-300 ${
          isExpanded ? 'w-80' : 'w-12'
        }`}>
          {/* Toggle Button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full p-3 flex items-center justify-center hover:bg-gray-700 rounded-lg"
            title="Debug Toolbar"
          >
            <span className="text-lg">🔧</span>
            {isExpanded && (
              <span className="ml-2 text-sm font-medium">Debug Tools</span>
            )}
          </button>

          {/* Expanded Content */}
          {isExpanded && (
            <div className="p-3 border-t border-gray-700">
              {/* Status Indicators */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-xs">
                  <span>API Health:</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${getHealthStatusColor()}`}></div>
                    <span>{getHealthStatusText()}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <span>Errors:</span>
                  <span className={`px-2 py-1 rounded ${
                    errorCount > 0 ? 'bg-red-600' : 'bg-gray-600'
                  }`}>
                    {errorCount}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span>Alerts:</span>
                  <span className={`px-2 py-1 rounded ${
                    alertCount > 0 ? 'bg-orange-600' : 'bg-gray-600'
                  }`}>
                    {alertCount}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2">
                <button
                  onClick={() => setIsConsoleOpen(true)}
                  className="w-full px-3 py-2 text-xs bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                >
                  Debug Console
                </button>

                <button
                  onClick={() => setIsDashboardOpen(true)}
                  className="w-full px-3 py-2 text-xs bg-purple-600 hover:bg-purple-700 rounded transition-colors"
                >
                  Performance Dashboard
                </button>
                
                <button
                  onClick={handleForceHealthCheck}
                  className="w-full px-3 py-2 text-xs bg-green-600 hover:bg-green-700 rounded transition-colors"
                >
                  Health Check
                </button>
                
                <div className="flex space-x-1">
                  <button
                    onClick={handleExportLogs}
                    className="flex-1 px-2 py-1 text-xs bg-gray-600 hover:bg-gray-700 rounded transition-colors"
                  >
                    Export
                  </button>
                  <button
                    onClick={handleClearLogs}
                    className="flex-1 px-2 py-1 text-xs bg-red-600 hover:bg-red-700 rounded transition-colors"
                  >
                    Clear
                  </button>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="mt-3 pt-3 border-t border-gray-700">
                <div className="text-xs text-gray-400">
                  <div>Logs: {apiLogger.getStats().total}</div>
                  <div>Avg Response: {Math.round(apiLogger.getStats().avgResponseTime)}ms</div>
                  <div>Error Rate: {apiLogger.getStats().errorRate.toFixed(1)}%</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Debug Console Modal */}
      <DebugConsole
        isOpen={isConsoleOpen}
        onClose={() => setIsConsoleOpen(false)}
      />

      {/* Performance Dashboard Modal */}
      <ApiPerformanceDashboard
        isOpen={isDashboardOpen}
        onClose={() => setIsDashboardOpen(false)}
      />
    </>
  );
};