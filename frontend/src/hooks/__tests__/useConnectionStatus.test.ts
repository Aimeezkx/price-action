/**
 * Unit tests for useConnectionStatus hook
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useConnectionStatus } from '../useConnectionStatus';
import { healthMonitor } from '../../lib/health-monitor';

// Mock the health monitor
vi.mock('../../lib/health-monitor', () => ({
  healthMonitor: {
    getCurrentStatus: vi.fn(),
    onHealthChange: vi.fn(),
    forceHealthCheck: vi.fn(),
    checkDetailedHealth: vi.fn(),
    getHealthStats: vi.fn(),
    startPeriodicChecks: vi.fn(),
    stopPeriodicChecks: vi.fn()
  }
}));

const mockHealthMonitor = healthMonitor as any;

describe('useConnectionStatus', () => {
  const mockHealthyStatus = {
    isHealthy: true,
    lastCheck: new Date('2023-01-01T12:00:00Z'),
    responseTime: 150,
    error: undefined
  };

  const mockUnhealthyStatus = {
    isHealthy: false,
    lastCheck: new Date('2023-01-01T12:00:00Z'),
    responseTime: 0,
    error: {
      type: 'CONNECTION_TIMEOUT',
      userMessage: 'Connection timeout',
      technicalMessage: 'Request timed out after 5000ms',
      canRetry: true
    }
  };

  const mockStats = {
    consecutiveFailures: 0,
    lastSuccessfulCheck: new Date(),
    isMonitoring: true,
    checkInterval: 30000,
    currentStatus: mockHealthyStatus
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockHealthMonitor.getCurrentStatus.mockReturnValue(mockHealthyStatus);
    mockHealthMonitor.onHealthChange.mockReturnValue(() => {}); // Unsubscribe function
    mockHealthMonitor.forceHealthCheck.mockResolvedValue(mockHealthyStatus);
    mockHealthMonitor.checkDetailedHealth.mockResolvedValue(mockHealthyStatus);
    mockHealthMonitor.getHealthStats.mockReturnValue(mockStats);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should return initial status', () => {
    const { result } = renderHook(() => useConnectionStatus());

    expect(result.current.status).toEqual(mockHealthyStatus);
    expect(result.current.isHealthy).toBe(true);
    expect(result.current.isChecking).toBe(false);
    expect(result.current.lastCheck).toEqual(mockHealthyStatus.lastCheck);
    expect(result.current.responseTime).toBe(150);
    expect(result.current.error).toBeUndefined();
    expect(result.current.stats).toEqual(mockStats);
    expect(result.current.isMonitoring).toBe(true);
  });

  it('should subscribe to health status changes', () => {
    renderHook(() => useConnectionStatus());

    expect(mockHealthMonitor.onHealthChange).toHaveBeenCalledTimes(1);
    expect(typeof mockHealthMonitor.onHealthChange.mock.calls[0][0]).toBe('function');
  });

  it('should update status when health changes', () => {
    let statusChangeCallback: (status: any) => void;
    mockHealthMonitor.onHealthChange.mockImplementation((callback) => {
      statusChangeCallback = callback;
      return () => {};
    });

    const { result } = renderHook(() => useConnectionStatus());

    // Initially healthy
    expect(result.current.isHealthy).toBe(true);

    // Simulate status change to unhealthy
    act(() => {
      statusChangeCallback!(mockUnhealthyStatus);
    });

    expect(result.current.status).toEqual(mockUnhealthyStatus);
    expect(result.current.isHealthy).toBe(false);
    expect(result.current.error).toEqual(mockUnhealthyStatus.error);
  });

  it('should handle checkHealth action', async () => {
    const { result } = renderHook(() => useConnectionStatus());

    expect(result.current.isChecking).toBe(false);

    await act(async () => {
      const status = await result.current.checkHealth();
      expect(status).toEqual(mockHealthyStatus);
    });

    expect(mockHealthMonitor.forceHealthCheck).toHaveBeenCalledTimes(1);
  });

  it('should handle checkDetailedHealth action', async () => {
    const { result } = renderHook(() => useConnectionStatus());

    await act(async () => {
      const status = await result.current.checkDetailedHealth();
      expect(status).toEqual(mockHealthyStatus);
    });

    expect(mockHealthMonitor.checkDetailedHealth).toHaveBeenCalledTimes(1);
  });

  it('should handle startMonitoring action', () => {
    const { result } = renderHook(() => useConnectionStatus());

    act(() => {
      result.current.startMonitoring();
    });

    expect(mockHealthMonitor.startPeriodicChecks).toHaveBeenCalledTimes(1);
  });

  it('should handle stopMonitoring action', () => {
    const { result } = renderHook(() => useConnectionStatus());

    act(() => {
      result.current.stopMonitoring();
    });

    expect(mockHealthMonitor.stopPeriodicChecks).toHaveBeenCalledTimes(1);
  });

  it('should set isChecking during health check', async () => {
    let resolveHealthCheck: (value: any) => void;
    const healthCheckPromise = new Promise(resolve => {
      resolveHealthCheck = resolve;
    });
    mockHealthMonitor.forceHealthCheck.mockReturnValue(healthCheckPromise);

    const { result } = renderHook(() => useConnectionStatus());

    expect(result.current.isChecking).toBe(false);

    // Start health check
    act(() => {
      result.current.checkHealth();
    });

    expect(result.current.isChecking).toBe(true);

    // Resolve health check
    await act(async () => {
      resolveHealthCheck!(mockHealthyStatus);
      await healthCheckPromise;
    });

    expect(result.current.isChecking).toBe(false);
  });

  it('should handle health check errors', async () => {
    mockHealthMonitor.forceHealthCheck.mockRejectedValue(new Error('Health check failed'));

    const { result } = renderHook(() => useConnectionStatus());

    await act(async () => {
      try {
        await result.current.checkHealth();
      } catch (error) {
        // Error should be handled gracefully
      }
    });

    expect(result.current.isChecking).toBe(false);
  });

  it('should update stats periodically', async () => {
    vi.useFakeTimers();
    
    const { result } = renderHook(() => useConnectionStatus());

    const initialStats = result.current.stats;

    // Update mock stats
    const updatedStats = { ...mockStats, consecutiveFailures: 1 };
    mockHealthMonitor.getHealthStats.mockReturnValue(updatedStats);

    // Fast-forward time to trigger stats update
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(result.current.stats).toEqual(updatedStats);

    vi.useRealTimers();
  });

  it('should cleanup on unmount', () => {
    const unsubscribe = vi.fn();
    mockHealthMonitor.onHealthChange.mockReturnValue(unsubscribe);

    const { unmount } = renderHook(() => useConnectionStatus());

    unmount();

    expect(unsubscribe).toHaveBeenCalledTimes(1);
  });

  it('should handle status change callback setting isChecking to false', () => {
    let statusChangeCallback: (status: any) => void;
    mockHealthMonitor.onHealthChange.mockImplementation((callback) => {
      statusChangeCallback = callback;
      return () => {};
    });

    const { result } = renderHook(() => useConnectionStatus());

    // Manually set isChecking to true
    act(() => {
      result.current.checkHealth();
    });

    // Simulate status change (should set isChecking to false)
    act(() => {
      statusChangeCallback!(mockHealthyStatus);
    });

    expect(result.current.isChecking).toBe(false);
  });
});