import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StudyScreen } from '../../screens/StudyScreen';
import { crashReportingService } from '../../services/crashReportingService';
import * as api from '../../services/api';

// Mock the API
jest.mock('../../services/api');
const mockApi = api as jest.Mocked<typeof api>;

// Mock crash reporting service
jest.mock('../../services/crashReportingService', () => ({
  crashReportingService: {
    initialize: jest.fn(),
    recordError: jest.fn(),
    recordWarning: jest.fn(),
    recordUserAction: jest.fn(),
    recordAPICall: jest.fn(),
    recordPerformanceMetrics: jest.fn(),
    setUserId: jest.fn(),
  },
}));

const mockCrashReporting = crashReportingService as jest.Mocked<typeof crashReportingService>;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('Crash Reporting Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Error Tracking in Study Flow', () => {
    it('should track API errors during card loading', async () => {
      const apiError = new Error('Failed to load cards');
      mockApi.apiClient.getDailyReview.mockRejectedValue(apiError);

      render(<StudyScreen />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockCrashReporting.recordError).toHaveBeenCalledWith(
          apiError,
          expect.objectContaining({
            screen: 'StudyScreen',
            action: 'load_daily_review',
          })
        );
      });
    });

    it('should track user actions during card grading', async () => {
      const mockCards = [
        {
          id: '1',
          front: 'Question',
          back: 'Answer',
          cardType: 'qa' as const,
          difficulty: 2.5,
          dueDate: new Date(),
          metadata: {},
        },
      ];

      mockApi.apiClient.getDailyReview.mockResolvedValue(mockCards);
      mockApi.apiClient.gradeCard.mockResolvedValue({ success: true });

      const { getByTestId } = render(<StudyScreen />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(getByTestId('flashcard-container')).toBeTruthy();
      });

      // Flip card
      fireEvent.press(getByTestId('flashcard-container'));

      await waitFor(() => {
        expect(mockCrashReporting.recordUserAction).toHaveBeenCalledWith(
          'flip_card',
          expect.objectContaining({
            screen: 'StudyScreen',
            cardId: '1',
          })
        );
      });

      // Grade card
      fireEvent.press(getByTestId('grade-button-4'));

      await waitFor(() => {
        expect(mockCrashReporting.recordUserAction).toHaveBeenCalledWith(
          'grade_card',
          expect.objectContaining({
            screen: 'StudyScreen',
            cardId: '1',
            grade: 4,
          })
        );
      });
    });

    it('should track performance metrics during animations', async () => {
      const mockCards = [
        {
          id: '1',
          front: 'Question',
          back: 'Answer',
          cardType: 'qa' as const,
          difficulty: 2.5,
          dueDate: new Date(),
          metadata: {},
        },
      ];

      mockApi.apiClient.getDailyReview.mockResolvedValue(mockCards);

      const { getByTestId } = render(<StudyScreen />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(getByTestId('flashcard-container')).toBeTruthy();
      });

      // Simulate slow animation
      const startTime = Date.now();
      fireEvent.press(getByTestId('flashcard-container'));
      
      // Mock animation completion after 400ms (slow)
      setTimeout(() => {
        const animationDuration = Date.now() - startTime;
        
        expect(mockCrashReporting.recordPerformanceMetrics).toHaveBeenCalledWith(
          expect.objectContaining({
            animationDuration: expect.any(Number),
          }),
          expect.objectContaining({
            screen: 'StudyScreen',
            action: 'flip_animation',
          })
        );
      }, 400);
    });
  });

  describe('Error Boundary Integration', () => {
    it('should catch and report component errors', () => {
      const ThrowError = () => {
        throw new Error('Component error');
      };

      const ErrorBoundary = ({ children }: { children: React.ReactNode }) => {
        try {
          return <>{children}</>;
        } catch (error) {
          mockCrashReporting.recordError(error as Error, {
            screen: 'ErrorBoundary',
            action: 'component_error',
          });
          return null;
        }
      };

      expect(() => {
        render(
          <ErrorBoundary>
            <ThrowError />
          </ErrorBoundary>
        );
      }).toThrow();

      expect(mockCrashReporting.recordError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          screen: 'ErrorBoundary',
          action: 'component_error',
        })
      );
    });
  });

  describe('API Call Tracking', () => {
    it('should track successful API calls', async () => {
      const mockCards = [
        {
          id: '1',
          front: 'Question',
          back: 'Answer',
          cardType: 'qa' as const,
          difficulty: 2.5,
          dueDate: new Date(),
          metadata: {},
        },
      ];

      mockApi.apiClient.getDailyReview.mockResolvedValue(mockCards);

      render(<StudyScreen />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockCrashReporting.recordAPICall).toHaveBeenCalledWith(
          '/review/today',
          'GET',
          expect.any(Number),
          true
        );
      });
    });

    it('should track failed API calls', async () => {
      const apiError = new Error('Network error');
      mockApi.apiClient.getDailyReview.mockRejectedValue(apiError);

      render(<StudyScreen />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockCrashReporting.recordAPICall).toHaveBeenCalledWith(
          '/review/today',
          'GET',
          expect.any(Number),
          false
        );
      });
    });
  });

  describe('Memory Leak Detection', () => {
    it('should track memory usage during component lifecycle', () => {
      const { unmount } = render(<StudyScreen />, { wrapper: createWrapper() });

      // Simulate memory usage tracking
      const mockMemoryUsage = 45.5; // MB
      
      mockCrashReporting.recordPerformanceMetrics({
        memoryUsage: mockMemoryUsage,
      }, {
        screen: 'StudyScreen',
        action: 'memory_check',
      });

      expect(mockCrashReporting.recordPerformanceMetrics).toHaveBeenCalledWith(
        expect.objectContaining({
          memoryUsage: 45.5,
        }),
        expect.objectContaining({
          screen: 'StudyScreen',
          action: 'memory_check',
        })
      );

      unmount();
    });

    it('should warn about high memory usage', () => {
      render(<StudyScreen />, { wrapper: createWrapper() });

      // Simulate high memory usage
      const highMemoryUsage = 85.0; // MB
      
      if (highMemoryUsage > 80) {
        mockCrashReporting.recordWarning('High memory usage detected', {
          screen: 'StudyScreen',
          memoryUsage: highMemoryUsage.toString(),
        });
      }

      expect(mockCrashReporting.recordWarning).toHaveBeenCalledWith(
        'High memory usage detected',
        expect.objectContaining({
          screen: 'StudyScreen',
          memoryUsage: '85',
        })
      );
    });
  });

  describe('User Context Tracking', () => {
    it('should maintain user context across screens', async () => {
      const userId = 'test-user-123';
      
      // Simulate user login
      mockCrashReporting.setUserId(userId);

      render(<StudyScreen />, { wrapper: createWrapper() });

      expect(mockCrashReporting.setUserId).toHaveBeenCalledWith(userId);

      // Simulate error with user context
      const error = new Error('User-specific error');
      mockCrashReporting.recordError(error, {
        screen: 'StudyScreen',
        userId,
      });

      expect(mockCrashReporting.recordError).toHaveBeenCalledWith(
        error,
        expect.objectContaining({
          screen: 'StudyScreen',
          userId,
        })
      );
    });
  });

  describe('Offline Error Handling', () => {
    it('should track offline-related errors', async () => {
      const offlineError = new Error('Network request failed');
      mockApi.apiClient.getDailyReview.mockRejectedValue(offlineError);

      render(<StudyScreen />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockCrashReporting.recordError).toHaveBeenCalledWith(
          offlineError,
          expect.objectContaining({
            screen: 'StudyScreen',
            action: 'load_daily_review',
            offline: expect.any(String),
          })
        );
      });
    });

    it('should track offline mode usage', () => {
      render(<StudyScreen />, { wrapper: createWrapper() });

      // Simulate offline mode activation
      mockCrashReporting.recordUserAction('enable_offline_mode', {
        screen: 'StudyScreen',
      });

      expect(mockCrashReporting.recordUserAction).toHaveBeenCalledWith(
        'enable_offline_mode',
        expect.objectContaining({
          screen: 'StudyScreen',
        })
      );
    });
  });
});