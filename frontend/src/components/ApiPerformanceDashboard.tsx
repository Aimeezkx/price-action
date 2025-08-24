import React, { useState, useEffect, useMemo } from 'react';
import { apiPerformanceMonitor, PerformanceDashboardData, PerformanceAlert, EndpointStats } from '../lib/api-performance-monitor';

interface ApiPerformanceDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ApiPerformanceDashboard: React.FC<ApiPerformanceDashboardProps> = ({ isOpen, onClose }) => {
  const [dashboardData, setDashboardData] = useState<PerformanceDashboardData | null>(null);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('24h');
  const [selectedEndpoint, setSelectedEndpoint] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number>(30000); // 30 seconds

  useEffect(() => {
    if (!isOpen) return;

    const loadData = () => {
      const timeRange = getTimeRange(selectedTimeRange);
      const data = apiPerformanceMonitor.getDashboardData(timeRange);
      const currentAlerts = apiPerformanceMonitor.getAlerts();
      
      setDashboardData(data);
      setAlerts(currentAlerts);
    };

    // Initial load
    loadData();

    // Set up refresh interval
    const interval = setInterval(loadData, refreshInterval);

    // Subscribe to new alerts
    const unsubscribe = apiPerformanceMonitor.onAlert((alert) => {
      setAlerts(prev => [alert, ...prev]);
    });

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [isOpen, selectedTimeRange, refreshInterval]);

  const getTimeRange = (range: string) => {
    const now = new Date();
    const hours = {
      '1h': 1,
      '6h': 6,
      '24h': 24,
      '7d': 24 * 7
    }[range] || 24;

    return {
      start: new Date(now.getTime() - hours * 60 * 60 * 1000),
      end: now
    };
  };

  const formatResponseTime = (time: number) => {
    if (time < 1000) return `${Math.round(time)}ms`;
    return `${(time / 1000).toFixed(1)}s`;
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getStatusColor = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return 'text-green-600 bg-green-50';
    if (value <= thresholds.warning) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getAlertSeverityColor = (severity: PerformanceAlert['severity']) => {
    switch (severity) {
      case 'low': return 'bg-blue-100 text-blue-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredEndpoints = useMemo(() => {
    if (!dashboardData || !selectedEndpoint) return dashboardData?.endpoints || [];
    return dashboardData.endpoints.filter(endpoint => 
      endpoint.endpoint.includes(selectedEndpoint)
    );
  }, [dashboardData, selectedEndpoint]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-7xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-4">
            <h2 className="text-2xl font-bold">API Performance Dashboard</h2>
            <div className="flex items-center space-x-2">
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value as any)}
                className="px-3 py-1 text-sm border rounded"
              >
                <option value="1h">Last Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
              </select>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                const data = apiPerformanceMonitor.exportData('json');
                const blob = new Blob([data], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `api-performance-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
              }}
              className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Export Data
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              Close
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {dashboardData ? (
            <div className="space-y-6">
              {/* Overview Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="text-sm font-medium text-gray-500">Total Requests</div>
                  <div className="text-2xl font-bold">{dashboardData.overview.totalRequests}</div>
                </div>
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="text-sm font-medium text-gray-500">Success Rate</div>
                  <div className={`text-2xl font-bold px-2 py-1 rounded ${
                    getStatusColor(dashboardData.overview.successRate, { good: 95, warning: 90 })
                  }`}>
                    {formatPercentage(dashboardData.overview.successRate)}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="text-sm font-medium text-gray-500">Avg Response Time</div>
                  <div className={`text-2xl font-bold px-2 py-1 rounded ${
                    getStatusColor(dashboardData.overview.avgResponseTime, { good: 500, warning: 1000 })
                  }`}>
                    {formatResponseTime(dashboardData.overview.avgResponseTime)}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="text-sm font-medium text-gray-500">Total Retries</div>
                  <div className="text-2xl font-bold">{dashboardData.overview.totalRetries}</div>
                </div>
              </div>

              {/* Alerts */}
              {alerts.length > 0 && (
                <div className="bg-white rounded-lg border shadow-sm">
                  <div className="p-4 border-b">
                    <h3 className="text-lg font-semibold">Recent Alerts</h3>
                  </div>
                  <div className="p-4">
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {alerts.slice(0, 10).map((alert) => (
                        <div key={alert.id} className="flex items-center justify-between p-3 rounded border">
                          <div className="flex items-center space-x-3">
                            <span className={`px-2 py-1 text-xs rounded ${getAlertSeverityColor(alert.severity)}`}>
                              {alert.severity.toUpperCase()}
                            </span>
                            <div>
                              <div className="font-medium">{alert.message}</div>
                              <div className="text-sm text-gray-500">{alert.endpoint}</div>
                            </div>
                          </div>
                          <div className="text-sm text-gray-500">
                            {alert.timestamp.toLocaleTimeString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Endpoint Filter */}
              <div className="bg-white rounded-lg border shadow-sm">
                <div className="p-4 border-b">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Endpoint Performance</h3>
                    <input
                      type="text"
                      placeholder="Filter endpoints..."
                      value={selectedEndpoint || ''}
                      onChange={(e) => setSelectedEndpoint(e.target.value || null)}
                      className="px-3 py-1 text-sm border rounded"
                    />
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Endpoint</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Requests</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Success Rate</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Response</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">P95</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Retries</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Request</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {filteredEndpoints.map((endpoint, index) => (
                        <tr key={`${endpoint.endpoint}-${endpoint.method}`} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-mono">{endpoint.endpoint}</td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 text-xs rounded ${
                              endpoint.method === 'GET' ? 'bg-green-100 text-green-800' :
                              endpoint.method === 'POST' ? 'bg-blue-100 text-blue-800' :
                              endpoint.method === 'PUT' ? 'bg-yellow-100 text-yellow-800' :
                              endpoint.method === 'DELETE' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {endpoint.method}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">{endpoint.totalRequests}</td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 rounded ${
                              getStatusColor(endpoint.successRate, { good: 95, warning: 90 })
                            }`}>
                              {formatPercentage(endpoint.successRate)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 rounded ${
                              getStatusColor(endpoint.avgResponseTime, { good: 500, warning: 1000 })
                            }`}>
                              {formatResponseTime(endpoint.avgResponseTime)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">{formatResponseTime(endpoint.p95ResponseTime)}</td>
                          <td className="px-4 py-3 text-sm">{endpoint.totalRetries}</td>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            {endpoint.lastRequest.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Slowest Endpoints */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg border shadow-sm">
                  <div className="p-4 border-b">
                    <h3 className="text-lg font-semibold">Slowest Endpoints</h3>
                  </div>
                  <div className="p-4">
                    <div className="space-y-3">
                      {dashboardData.slowestEndpoints.map((endpoint, index) => (
                        <div key={`slow-${endpoint.endpoint}-${endpoint.method}`} className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{endpoint.endpoint}</div>
                            <div className="text-xs text-gray-500">{endpoint.method}</div>
                          </div>
                          <div className="text-sm font-medium">
                            {formatResponseTime(endpoint.avgResponseTime)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg border shadow-sm">
                  <div className="p-4 border-b">
                    <h3 className="text-lg font-semibold">Most Error-Prone Endpoints</h3>
                  </div>
                  <div className="p-4">
                    <div className="space-y-3">
                      {dashboardData.mostErrorProneEndpoints.map((endpoint, index) => (
                        <div key={`error-${endpoint.endpoint}-${endpoint.method}`} className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{endpoint.endpoint}</div>
                            <div className="text-xs text-gray-500">{endpoint.method}</div>
                          </div>
                          <div className="text-sm font-medium text-red-600">
                            {formatPercentage(endpoint.errorRate)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="text-lg font-medium text-gray-900">Loading performance data...</div>
                <div className="text-sm text-gray-500">Please wait while we gather metrics</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};