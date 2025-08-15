import React, { useState, useEffect } from 'react';
import { performanceMonitor } from '../lib/performance';

interface PerformanceStats {
  count: number;
  total: number;
  min: number;
  max: number;
  avg: number;
}

interface PerformanceSummary {
  [key: string]: PerformanceStats;
}

export function PerformanceDashboard() {
  const [summary, setSummary] = useState<PerformanceSummary>({});
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const updateSummary = () => {
      setSummary(performanceMonitor.getPerformanceSummary());
    };

    // Update every 5 seconds
    const interval = setInterval(updateSummary, 5000);
    updateSummary(); // Initial update

    return () => clearInterval(interval);
  }, []);

  const formatValue = (value: number, metric: string) => {
    if (metric === 'CLS') {
      return value.toFixed(3);
    }
    return `${Math.round(value)}ms`;
  };

  const getStatusColor = (metric: string, value: number) => {
    const thresholds: Record<string, { warning: number; critical: number }> = {
      'PageLoad': { warning: 1000, critical: 2000 },
      'LCP': { warning: 2000, critical: 2500 },
      'FID': { warning: 50, critical: 100 },
      'CLS': { warning: 0.05, critical: 0.1 },
      'ComponentRender': { warning: 10, critical: 16 },
      'APICall': { warning: 500, critical: 1000 }
    };

    const threshold = thresholds[metric];
    if (!threshold) return 'text-gray-600';

    if (value >= threshold.critical) return 'text-red-600';
    if (value >= threshold.warning) return 'text-yellow-600';
    return 'text-green-600';
  };

  const exportData = () => {
    const data = performanceMonitor.exportMetrics();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `performance-metrics-${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 bg-blue-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors z-50"
        title="Show Performance Dashboard"
      >
        📊 Perf
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md z-50">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-gray-800">Performance Monitor</h3>
        <div className="flex gap-2">
          <button
            onClick={exportData}
            className="text-blue-600 hover:text-blue-800 text-sm"
            title="Export Metrics"
          >
            📥
          </button>
          <button
            onClick={() => setIsVisible(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {Object.entries(summary).map(([metric, stats]) => (
          <div key={metric} className="text-sm">
            <div className="flex justify-between items-center">
              <span className="font-medium text-gray-700">{metric}</span>
              <span className={`font-mono ${getStatusColor(metric, stats.avg)}`}>
                {formatValue(stats.avg, metric)}
              </span>
            </div>
            <div className="text-xs text-gray-500 flex justify-between">
              <span>Count: {stats.count}</span>
              <span>
                Min: {formatValue(stats.min, metric)} | 
                Max: {formatValue(stats.max, metric)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {Object.keys(summary).length === 0 && (
        <div className="text-sm text-gray-500 text-center py-4">
          No performance data yet
        </div>
      )}
    </div>
  );
}