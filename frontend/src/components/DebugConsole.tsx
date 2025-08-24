import React, { useState, useEffect, useMemo } from 'react';
import { apiLogger, LogEntry, LogLevel, LogCategory, LogFilter } from '../lib/api-logger';

interface DebugConsoleProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DebugConsole: React.FC<DebugConsoleProps> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<LogFilter>({});
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (!isOpen) return;

    // Initial load
    setLogs(apiLogger.getLogs(filter));

    // Subscribe to new logs
    const unsubscribe = apiLogger.subscribe((entry) => {
      if (autoScroll) {
        setLogs(prev => [entry, ...prev]);
      }
    });

    return unsubscribe;
  }, [isOpen, filter, autoScroll]);

  const stats = useMemo(() => apiLogger.getStats(), [logs]);

  const filteredLogs = useMemo(() => {
    return apiLogger.getLogs(filter);
  }, [filter, logs]);

  const handleExportLogs = () => {
    const logsJson = apiLogger.exportLogs(filter);
    const blob = new Blob([logsJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api-logs-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleClearLogs = () => {
    apiLogger.clearLogs();
    setLogs([]);
    setSelectedLog(null);
  };

  const getLogLevelColor = (level: LogLevel): string => {
    switch (level) {
      case LogLevel.ERROR:
        return 'text-red-600 bg-red-50';
      case LogLevel.WARN:
        return 'text-yellow-600 bg-yellow-50';
      case LogLevel.INFO:
        return 'text-blue-600 bg-blue-50';
      case LogLevel.DEBUG:
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getCategoryIcon = (category: LogCategory): string => {
    switch (category) {
      case LogCategory.API_REQUEST:
        return '→';
      case LogCategory.API_RESPONSE:
        return '←';
      case LogCategory.NETWORK_ERROR:
        return '⚠';
      case LogCategory.RETRY_ATTEMPT:
        return '↻';
      case LogCategory.HEALTH_CHECK:
        return '♥';
      case LogCategory.CONNECTION_STATUS:
        return '🔗';
      default:
        return '•';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold">API Debug Console</h2>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>Total: {stats.total}</span>
              <span>Errors: {stats.byLevel[LogLevel.ERROR]}</span>
              <span>Error Rate: {stats.errorRate.toFixed(1)}%</span>
              <span>Avg Response: {stats.avgResponseTime.toFixed(0)}ms</span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleExportLogs}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Export
            </button>
            <button
              onClick={handleClearLogs}
              className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
            >
              Clear
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              Close
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 border-b bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Level
              </label>
              <select
                multiple
                className="w-full text-sm border rounded px-2 py-1"
                value={filter.level || []}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value as LogLevel);
                  setFilter(prev => ({ ...prev, level: values.length > 0 ? values : undefined }));
                }}
              >
                {Object.values(LogLevel).map(level => (
                  <option key={level} value={level}>
                    {level.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                multiple
                className="w-full text-sm border rounded px-2 py-1"
                value={filter.category || []}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value as LogCategory);
                  setFilter(prev => ({ ...prev, category: values.length > 0 ? values : undefined }));
                }}
              >
                {Object.values(LogCategory).map(category => (
                  <option key={category} value={category}>
                    {category.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search
              </label>
              <input
                type="text"
                className="w-full text-sm border rounded px-2 py-1"
                placeholder="Search logs..."
                value={filter.searchTerm || ''}
                onChange={(e) => setFilter(prev => ({ ...prev, searchTerm: e.target.value || undefined }))}
              />
            </div>

            <div className="flex items-end space-x-2">
              <label className="flex items-center text-sm">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="mr-1"
                />
                Auto-scroll
              </label>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Log List */}
          <div className="w-1/2 border-r overflow-y-auto">
            <div className="divide-y">
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className={`p-3 cursor-pointer hover:bg-gray-50 ${
                    selectedLog?.id === log.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                  }`}
                  onClick={() => setSelectedLog(log)}
                >
                  <div className="flex items-start space-x-2">
                    <span className="text-lg">{getCategoryIcon(log.category)}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`px-2 py-1 text-xs rounded ${getLogLevelColor(log.level)}`}>
                          {log.level.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-500">
                          {log.timestamp.toLocaleTimeString()}
                        </span>
                        {log.responseTime && (
                          <span className="text-xs text-gray-500">
                            {log.responseTime}ms
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-900 truncate">
                        {log.message}
                      </div>
                      {log.url && (
                        <div className="text-xs text-gray-500 truncate">
                          {log.method} {log.url}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Log Details */}
          <div className="w-1/2 overflow-y-auto">
            {selectedLog ? (
              <div className="p-4">
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-lg mb-2">Log Details</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">ID:</span> {selectedLog.id}
                      </div>
                      <div>
                        <span className="font-medium">Timestamp:</span> {selectedLog.timestamp.toISOString()}
                      </div>
                      <div>
                        <span className="font-medium">Level:</span> {selectedLog.level}
                      </div>
                      <div>
                        <span className="font-medium">Category:</span> {selectedLog.category}
                      </div>
                      {selectedLog.requestId && (
                        <div className="col-span-2">
                          <span className="font-medium">Request ID:</span> {selectedLog.requestId}
                        </div>
                      )}
                      {selectedLog.url && (
                        <div className="col-span-2">
                          <span className="font-medium">URL:</span> {selectedLog.url}
                        </div>
                      )}
                      {selectedLog.method && (
                        <div>
                          <span className="font-medium">Method:</span> {selectedLog.method}
                        </div>
                      )}
                      {selectedLog.statusCode && (
                        <div>
                          <span className="font-medium">Status:</span> {selectedLog.statusCode}
                        </div>
                      )}
                      {selectedLog.responseTime && (
                        <div>
                          <span className="font-medium">Response Time:</span> {selectedLog.responseTime}ms
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">Message</h4>
                    <div className="bg-gray-100 p-3 rounded text-sm">
                      {selectedLog.message}
                    </div>
                  </div>

                  {selectedLog.error && (
                    <div>
                      <h4 className="font-medium mb-2">Error Details</h4>
                      <div className="bg-red-50 p-3 rounded text-sm">
                        <div><strong>Name:</strong> {selectedLog.error.name}</div>
                        <div><strong>Message:</strong> {selectedLog.error.message}</div>
                        {selectedLog.error.code && (
                          <div><strong>Code:</strong> {selectedLog.error.code}</div>
                        )}
                        {selectedLog.error.stack && (
                          <div className="mt-2">
                            <strong>Stack Trace:</strong>
                            <pre className="text-xs mt-1 whitespace-pre-wrap">
                              {selectedLog.error.stack}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {selectedLog.data && (
                    <div>
                      <h4 className="font-medium mb-2">Additional Data</h4>
                      <div className="bg-gray-100 p-3 rounded text-sm">
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(selectedLog.data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-4 text-center text-gray-500">
                Select a log entry to view details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};