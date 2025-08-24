/**
 * Offline Indicator Component Tests
 * Tests for the offline indicator component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import OfflineIndicator from '../OfflineIndicator';
import * as useOfflineModeHook from '../../hooks/useOfflineMode';

// Mock the useOfflineMode hook
const mockUseOfflineMode = jest.spyOn(useOfflineModeHook, 'useOfflineMode');

describe('OfflineIndicator', () => {
  const mockProcessQueue = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not render when online with no queued actions', () => {
    mockUseOfflineMode.mockReturnValue({
      isOnline: true,
      isOffline: false,
      connectionQuality: 'good',
      state: {
        isOnline: true,
        lastOnlineTime: new Date(),
        connectionType: 'online',
        networkSpeed: 10
      },
      queueStats: {
        total: 0,
        byType: {},
        byPriority: {},
        oldestAction: null
      },
      processQueue: mockProcessQueue,
      queuedActions: [],
      addToQueue: jest.fn(),
      removeFromQueue: jest.fn(),
      clearQueue: jest.fn(),
      cacheData: jest.fn(),
      getCachedData: jest.fn(),
      clearCache: jest.fn()
    });

    const { container } = render(<OfflineIndicator />);
    expect(container.firstChild).toBeNull();
  });

  it('renders offline indicator when offline', () => {
    mockUseOfflineMode.mockReturnValue({
      isOnline: false,
      isOffline: true,
      connectionQuality: 'offline',
      state: {
        isOnline: false,
        lastOnlineTime: new Date(Date.now() - 60000), // 1 minute ago
        connectionType: 'offline',
        networkSpeed: null
      },
      queueStats: {
        total: 2,
        byType: { upload: 1, api_call: 1 },
        byPriority: { high: 1, medium: 1 },
        oldestAction: new Date()
      },
      processQueue: mockProcessQueue,
      queuedActions: [],
      addToQueue: jest.fn(),
      removeFromQueue: jest.fn(),
      clearQueue: jest.fn(),
      cacheData: jest.fn(),
      getCachedData: jest.fn(),
      clearCache: jest.fn()
    });

    render(<OfflineIndicator />);

    expect(screen.getByText('Offline')).toBeInTheDocument();
    expect(screen.getByText('2 queued')).toBeInTheDocument();
    expect(screen.getByLabelText('Connection status')).toHaveTextContent('📡');
  });

  it('renders poor connection indicator', () => {
    mockUseOfflineMode.mockReturnValue({
      isOnline: true,
      isOffline: false,
      connectionQuality: 'poor',
      state: {
        isOnline: true,
        lastOnlineTime: new Date(),
        connectionType: 'slow',
        networkSpeed: 0.5
      },
      queueStats: {
        total: 0,
        byType: {},
        byPriority: {},
        oldestAction: null
      },
      processQueue: mockProcessQueue,
      queuedActions: [],
      addToQueue: jest.fn(),
      removeFromQueue: jest.fn(),
      clearQueue: jest.fn(),
      cacheData: jest.fn(),
      getCachedData: jest.fn(),
      clearCache: jest.fn()
    });

    render(<OfflineIndicator showDetails />);

    expect(screen.getByText('Poor Connection')).toBeInTheDocument();
    expect(screen.getByText('0.5 Mbps')).toBeInTheDocument();
    expect(screen.getByLabelText('Connection status')).toHaveTextContent('⚠️');
  });

  it('shows process queue button when online with queued actions', () => {
    mockUseOfflineMode.mockReturnValue({
      isOnline: true,
      isOffline: false,
      connectionQuality: 'good',
      state: {
        isOnline: true,
        lastOnlineTime: new Date(),
        connectionType: 'online',
        networkSpeed: 10
      },
      queueStats: {
        total: 3,
        byType: { upload: 2, api_call: 1 },
        byPriority: { high: 2, medium: 1 },
        oldestAction: new Date()
      },
      processQueue: mockProcessQueue,
      queuedActions: [],
      addToQueue: jest.fn(),
      removeFromQueue: jest.fn(),
      clearQueue: jest.fn(),
      cacheData: jest.fn(),
      getCachedData: jest.fn(),
      clearCache: jest.fn()
    });

    render(<OfflineIndicator />);

    const processButton = screen.getByText('Process Queue');
    expect(processButton).toBeInTheDocument();

    fireEvent.click(processButton);
    expect(mockProcessQueue).toHaveBeenCalledTimes(1);
  });

  it('expands to show detailed information', () => {
    mockUseOfflineMode.mockReturnValue({
      isOnline: false,
      isOffline: true,
      connectionQuality: 'offline',
      state: {
        isOnline: false,
        lastOnlineTime: new Date(Date.now() - 3600000), // 1 hour ago
        connectionType: 'offline',
        networkSpeed: null
      },
      queueStats: {
        total: 5,
        byType: { upload: 3, api_call: 2 },
        byPriority: { high: 2, medium: 2, low: 1 },
        oldestAction: new Date()
      },
      processQueue: mockProcessQueue,
      queuedActions: [],
      addToQueue: jest.fn(),
      removeFromQueue: jest.fn(),
      clearQueue: jest.fn(),
      cacheData: jest.fn(),
      getCachedData: jest.fn(),
      clearCache: jest.fn()
    });

    render(<OfflineIndicator showDetails />);

    const expandButton = screen.getByText('▼');
    fireEvent.click(expandButton);

    expect(screen.getByText('Connection Info')).toBeInTheDocument();
    expect(screen.getByText('Queued Actions')).toBeInTheDocument();
    expect(screen.getByText('Status: offline')).toBeInTheDocument();
    expect(screen.getByText('Total: 5')).toBeInTheDocument();
    expect(screen.getByText('upload: 3')).toBeInTheDocument();
    expect(screen.getByText('api_call: 2')).toBeInTheDocument();
  });

  it('applies correct styling based on connection status', () => {
    const testCases = [
      { 
        isOnline: false, 
        connectionQuality: 'offline' as const, 
        expectedClass: 'bg-red-500' 
      },
      { 
        isOnline: true, 
        connectionQuality: 'poor' as const, 
        expectedClass: 'bg-yellow-500' 
      },
      { 
        isOnline: true, 
        connectionQuality: 'good' as const, 
        expectedClass: 'bg-green-500' 
      }
    ];

    testCases.forEach(({ isOnline, connectionQuality, expectedClass }) => {
      mockUseOfflineMode.mockReturnValue({
        isOnline,
        isOffline: !isOnline,
        connectionQuality,
        state: {
          isOnline,
          lastOnlineTime: new Date(),
          connectionType: isOnline ? 'online' : 'offline',
          networkSpeed: isOnline ? 10 : null
        },
        queueStats: {
          total: 1, // Show indicator
          byType: {},
          byPriority: {},
          oldestAction: null
        },
        processQueue: mockProcessQueue,
        queuedActions: [],
        addToQueue: jest.fn(),
        removeFromQueue: jest.fn(),
        clearQueue: jest.fn(),
        cacheData: jest.fn(),
        getCachedData: jest.fn(),
        clearCache: jest.fn()
      });

      const { container, unmount } = render(<OfflineIndicator />);
      const indicator = container.querySelector(`.${expectedClass}`);
      expect(indicator).toBeInTheDocument();
      unmount();
    });
  });

  it('formats last online time correctly', () => {
    const testCases = [
      { minutesAgo: 1, expected: '1 minute ago' },
      { minutesAgo: 30, expected: '30 minutes ago' },
      { minutesAgo: 90, expected: '1 hour ago' },
      { minutesAgo: 1440, expected: '1 day ago' }
    ];

    testCases.forEach(({ minutesAgo, expected }) => {
      mockUseOfflineMode.mockReturnValue({
        isOnline: false,
        isOffline: true,
        connectionQuality: 'offline',
        state: {
          isOnline: false,
          lastOnlineTime: new Date(Date.now() - minutesAgo * 60000),
          connectionType: 'offline',
          networkSpeed: null
        },
        queueStats: {
          total: 1,
          byType: {},
          byPriority: {},
          oldestAction: null
        },
        processQueue: mockProcessQueue,
        queuedActions: [],
        addToQueue: jest.fn(),
        removeFromQueue: jest.fn(),
        clearQueue: jest.fn(),
        cacheData: jest.fn(),
        getCachedData: jest.fn(),
        clearCache: jest.fn()
      });

      const { unmount } = render(<OfflineIndicator showDetails />);
      
      // Expand to see details
      const expandButton = screen.getByText('▼');
      fireEvent.click(expandButton);

      expect(screen.getByText(`Last online: ${expected}`)).toBeInTheDocument();
      unmount();
    });
  });
});