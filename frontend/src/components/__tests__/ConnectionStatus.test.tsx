/**
 * Unit tests for ConnectionStatus components
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ConnectionStatus, ConnectionIndicator, ConnectionStatusPanel } from '../ConnectionStatus';
import { healthMonitor } from '../../lib/health-monitor';

// Mock the health monitor
vi.mock('../../lib/health-monitor', () => ({
  healthMonitor: {
    getCurrentStatus: vi.fn(),
    onHealthChange: vi.fn(),
    forceHealthCheck: vi.fn(),
    checkDetailedHealth: vi.fn(),
    getHealthStats: vi.fn()
  }
}));

const mockHealthMonitor = healthMonitor as any;

describe('ConnectionStatus', () => {
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

  beforeEach(() => {
    vi.clearAllMocks();
    mockHealthMonitor.getCurrentStatus.mockReturnValue(mockHealthyStatus);
    mockHealthMonitor.onHealthChange.mockReturnValue(() => {}); // Unsubscribe function
    mockHealthMonitor.forceHealthCheck.mockResolvedValue(mockHealthyStatus);
    mockHealthMonitor.checkDetailedHealth.mockResolvedValue(mockHealthyStatus);
    mockHealthMonitor.getHealthStats.mockReturnValue({
      consecutiveFailures: 0,
      lastSuccessfulCheck: new Date(),
      isMonitoring: true,
      checkInterval: 30000,
      currentStatus: mockHealthyStatus
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('ConnectionStatus', () => {
    it('should render healthy status correctly', () => {
      render(<ConnectionStatus />);
      
      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.getByText('(150ms)')).toBeInTheDocument();
      expect(screen.queryByText('Retry')).not.toBeInTheDocument();
    });

    it('should render unhealthy status correctly', () => {
      mockHealthMonitor.getCurrentStatus.mockReturnValue(mockUnhealthyStatus);
      
      render(<ConnectionStatus />);
      
      expect(screen.getByText('Connection timeout')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should handle retry button click', async () => {
      mockHealthMonitor.getCurrentStatus.mockReturnValue(mockUnhealthyStatus);
      
      render(<ConnectionStatus />);
      
      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);
      
      expect(mockHealthMonitor.forceHealthCheck).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Checking...')).toBeInTheDocument();
    });

    it('should show details when showDetails is true', () => {
      render(<ConnectionStatus showDetails />);
      
      expect(screen.getByText('Details')).toBeInTheDocument();
    });

    it('should toggle detailed information', async () => {
      render(<ConnectionStatus showDetails />);
      
      const detailsButton = screen.getByText('Details');
      fireEvent.click(detailsButton);
      
      expect(screen.getByText('Hide Details')).toBeInTheDocument();
      expect(screen.getByText('Last Check:')).toBeInTheDocument();
      expect(screen.getByText('Response Time:')).toBeInTheDocument();
      expect(mockHealthMonitor.checkDetailedHealth).toHaveBeenCalledTimes(1);
    });

    it('should show error details when unhealthy', () => {
      mockHealthMonitor.getCurrentStatus.mockReturnValue(mockUnhealthyStatus);
      
      render(<ConnectionStatus showDetails />);
      
      const detailsButton = screen.getByText('Details');
      fireEvent.click(detailsButton);
      
      expect(screen.getByText('Error Type:')).toBeInTheDocument();
      expect(screen.getByText('CONNECTION_TIMEOUT')).toBeInTheDocument();
      expect(screen.getByText('Request timed out after 5000ms')).toBeInTheDocument();
    });

    it('should render in compact mode', () => {
      render(<ConnectionStatus compact />);
      
      // Should not show text in compact mode
      expect(screen.queryByText('Connected')).not.toBeInTheDocument();
      // Should show retry button for unhealthy status
      mockHealthMonitor.getCurrentStatus.mockReturnValue(mockUnhealthyStatus);
    });

    it('should subscribe to health status changes', () => {
      render(<ConnectionStatus />);
      
      expect(mockHealthMonitor.onHealthChange).toHaveBeenCalledTimes(1);
      expect(typeof mockHealthMonitor.onHealthChange.mock.calls[0][0]).toBe('function');
    });

    it('should update status when health changes', () => {
      let statusChangeCallback: (status: any) => void;
      mockHealthMonitor.onHealthChange.mockImplementation((callback) => {
        statusChangeCallback = callback;
        return () => {};
      });

      render(<ConnectionStatus />);
      
      // Initially healthy
      expect(screen.getByText('Connected')).toBeInTheDocument();
      
      // Simulate status change to unhealthy
      statusChangeCallback!(mockUnhealthyStatus);
      
      expect(screen.getByText('Connection timeout')).toBeInTheDocument();
    });

    it('should format response time correctly', () => {
      const statusWithLongResponseTime = {
        ...mockHealthyStatus,
        responseTime: 2500 // 2.5 seconds
      };
      mockHealthMonitor.getCurrentStatus.mockReturnValue(statusWithLongResponseTime);
      
      render(<ConnectionStatus />);
      
      expect(screen.getByText('(2.5s)')).toBeInTheDocument();
    });

    it('should handle health check errors gracefully', async () => {
      mockHealthMonitor.getCurrentStatus.mockReturnValue(mockUnhealthyStatus);
      mockHealthMonitor.forceHealthCheck.mockRejectedValue(new Error('Health check failed'));
      
      render(<ConnectionStatus />);
      
      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);
      
      await waitFor(() => {
        expect(mockHealthMonitor.forceHealthCheck).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('ConnectionIndicator', () => {
    it('should render in compact mode', () => {
      render(<ConnectionIndicator />);
      
      // Should not show text in compact mode
      expect(screen.queryByText('Connected')).not.toBeInTheDocument();
      // Should show icon
      expect(screen.getByRole('button', { name: /retry/i })).not.toBeInTheDocument();
    });

    it('should show retry button when unhealthy', () => {
      mockHealthMonitor.getCurrentStatus.mockReturnValue(mockUnhealthyStatus);
      
      render(<ConnectionIndicator />);
      
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  describe('ConnectionStatusPanel', () => {
    it('should render with details enabled', () => {
      render(<ConnectionStatusPanel />);
      
      expect(screen.getByText('Details')).toBeInTheDocument();
    });

    it('should show system status when details are expanded', () => {
      const statusWithDetails = {
        ...mockHealthyStatus,
        details: {
          status: 'healthy',
          timestamp: '2023-01-01T12:00:00Z',
          services: {
            database: { status: 'healthy' },
            redis: { status: 'healthy' }
          }
        }
      };
      mockHealthMonitor.getCurrentStatus.mockReturnValue(statusWithDetails);
      
      render(<ConnectionStatusPanel />);
      
      const detailsButton = screen.getByText('Details');
      fireEvent.click(detailsButton);
      
      expect(screen.getByText('System Status:')).toBeInTheDocument();
    });
  });
});