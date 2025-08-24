/**
 * React hook for connection status monitoring
 * Provides easy access to health status and control functions
 */

import { useState, useEffect, useCallback } from 'react';
import { healthMonitor, type HealthStatus } from '../lib/health-monitor';

export interface UseConnectionStatusReturn {
  status: HealthStatus;
  isHealthy: boolean;
  isChecking: boolean;
  lastCheck: Date;
  responseTime: number;
  error: HealthStatus['error'];
  stats: ReturnType<typeof healthMonitor.getHealthStats>;
  
  // Actions
  checkHealth: () => Promise<HealthStatus>;
  checkDetailedHealth: () => Promise<HealthStatus>;
  startMonitoring: () => void;
  stopMonitoring: () => void;
  isMonitoring: boolean;
}

export function useConnectionStatus(): UseConnectionStatusReturn {
  const [status, setStatus] = useState<HealthStatus>(healthMonitor.getCurrentStatus());
  const [isChecking, setIsChecking] = useState(false);
  const [stats, setStats] = useState(healthMonitor.getHealthStats());

  // Update stats periodically
  useEffect(() => {
    const updateStats = () => {
      setStats(healthMonitor.getHealthStats());
    };

    const interval = setInterval(updateStats, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Subscribe to health status changes
    const unsubscribe = healthMonitor.onHealthChange((newStatus) => {
      setStatus(newStatus);
      setIsChecking(false);
      setStats(healthMonitor.getHealthStats());
    });

    // Get initial status
    setStatus(healthMonitor.getCurrentStatus());
    setStats(healthMonitor.getHealthStats());

    return unsubscribe;
  }, []);

  const checkHealth = useCallback(async () => {
    setIsChecking(true);
    try {
      const result = await healthMonitor.forceHealthCheck();
      return result;
    } finally {
      setIsChecking(false);
    }
  }, []);

  const checkDetailedHealth = useCallback(async () => {
    setIsChecking(true);
    try {
      const result = await healthMonitor.checkDetailedHealth();
      return result;
    } finally {
      setIsChecking(false);
    }
  }, []);

  const startMonitoring = useCallback(() => {
    healthMonitor.startPeriodicChecks();
    setStats(healthMonitor.getHealthStats());
  }, []);

  const stopMonitoring = useCallback(() => {
    healthMonitor.stopPeriodicChecks();
    setStats(healthMonitor.getHealthStats());
  }, []);

  return {
    status,
    isHealthy: status.isHealthy,
    isChecking,
    lastCheck: status.lastCheck,
    responseTime: status.responseTime,
    error: status.error,
    stats,
    
    // Actions
    checkHealth,
    checkDetailedHealth,
    startMonitoring,
    stopMonitoring,
    isMonitoring: stats.isMonitoring,
  };
}