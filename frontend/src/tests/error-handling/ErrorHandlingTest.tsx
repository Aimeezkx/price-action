/**
 * Frontend Error Handling and Recovery Tests
 * 
 * This module tests error handling scenarios in the React frontend,
 * including network failures, invalid inputs, and graceful degradation.
 * 
 * Requirements covered: 6.1, 6.2, 6.3, 6.4, 6.5
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

// Mock components for testing
import DocumentUpload from '../../components/DocumentUpload';
import SearchComponent from '../../components/Search';
import FlashcardReview from '../../components/FlashcardReview';
import ErrorBoundary from '../../components/ErrorBoundary';
import OfflineIndicator from '../../components/OfflineIndicator';

// Mock API functions
import * as api from '../../services/api';

// Test utilities
import { createMockDocument, createMockCard, createMockSearchResults } from '../utils/mockData';

// Error simulation utilities
class FrontendErrorSimulator {
  private originalFetch: typeof global.fetch;
  private networkFailureActive = false;
  private slowNetworkActive = false;

  constructor() {
    this.originalFetch = global.fetch;
  }

  simulateNetworkFailure() {
    this.networkFailureActive = true;
    global.fetch = vi.fn().mockRejectedValue(new Error('Network Error'));
  }

  simulateSlowNetwork(delay: number = 5000) {
    this.slowNetworkActive = true;
    global.fetch = vi.fn().mockImplementation(
      () => new Promise((resolve) => {
        setTimeout(() => {
          resolve(new Response(JSON.stringify({ data: 'success' }), { status: 200 }));
        }, delay);
      })
    );
  }

  simulateIntermittentFailure(failureRate: number = 0.5) {
    global.fetch = vi.fn().mockImplementation(() => {
      if (Math.random() < failureRate) {
        return Promise.reject(new Error('Intermittent Network Error'));
      }
      return Promise.resolve(new Response(JSON.stringify({ data: 'success' }), { status: 200 }));
    });
  }

  simulateServerError(statusCode: number = 500) {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: 'Server Error' }), { status: statusCode })
    );
  }

  restoreNetwork() {
    this.networkFailureActive = false;
    this.slowNetworkActive = false;
    global.fetch = this.originalFetch;
  }

  isNetworkDown() {
    return this.networkFailureActive;
  }

  isNetworkSlow() {
    return this.slowNetworkActive;
  }
}

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Frontend Error Handling Tests', () => {
  let errorSimulator: FrontendErrorSimulator;
  let consoleErrorSpy: any;

  beforeEach(() => {
    errorSimulator = new FrontendErrorSimulator();
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    errorSimulator.restoreNetwork();
    consoleErrorSpy.mockRestore();
    vi.clearAllMocks();
  });

  describe('Document Upload Error Handling', () => {
    it('should handle file upload network failures gracefully', async () => {
      errorSimulator.simulateNetworkFailure();

      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/upload document/i);
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      await userEvent.upload(fileInput, file);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await userEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
        expect(screen.getByText(/please try again/i)).toBeInTheDocument();
      });

      // Should show retry option
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('should validate file types and show helpful error messages', async () => {
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/upload document/i);
      const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });

      await userEvent.upload(fileInput, invalidFile);

      await waitFor(() => {
        expect(screen.getByText(/unsupported file format/i)).toBeInTheDocument();
        expect(screen.getByText(/please select a pdf/i)).toBeInTheDocument();
      });
    });

    it('should handle oversized files with clear error messages', async () => {
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/upload document/i);
      // Create a mock large file
      const largeFile = new File(['x'.repeat(100 * 1024 * 1024)], 'large.pdf', { 
        type: 'application/pdf' 
      });
      Object.defineProperty(largeFile, 'size', { value: 100 * 1024 * 1024 });

      await userEvent.upload(fileInput, largeFile);

      await waitFor(() => {
        expect(screen.getByText(/file too large/i)).toBeInTheDocument();
        expect(screen.getByText(/maximum size is/i)).toBeInTheDocument();
      });
    });

    it('should show progress and allow cancellation during upload', async () => {
      errorSimulator.simulateSlowNetwork(10000); // 10 second delay

      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/upload document/i);
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      await userEvent.upload(fileInput, file);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await userEvent.click(uploadButton);

      // Should show progress indicator
      await waitFor(() => {
        expect(screen.getByText(/uploading/i)).toBeInTheDocument();
      });

      // Should show cancel button
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      expect(cancelButton).toBeInTheDocument();

      await userEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.getByText(/upload cancelled/i)).toBeInTheDocument();
      });
    });
  });

  describe('Search Error Handling', () => {
    it('should handle search API failures with fallback', async () => {
      errorSimulator.simulateServerError(503);

      render(
        <TestWrapper>
          <SearchComponent />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.type(searchInput, 'test query');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/search service temporarily unavailable/i)).toBeInTheDocument();
        expect(screen.getByText(/try basic search/i)).toBeInTheDocument();
      });

      // Should offer fallback search option
      const fallbackButton = screen.getByRole('button', { name: /basic search/i });
      expect(fallbackButton).toBeInTheDocument();
    });

    it('should validate empty search queries', async () => {
      render(
        <TestWrapper>
          <SearchComponent />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.click(searchInput);
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/please enter a search term/i)).toBeInTheDocument();
      });
    });

    it('should handle search timeout with retry option', async () => {
      errorSimulator.simulateSlowNetwork(30000); // 30 second timeout

      render(
        <TestWrapper>
          <SearchComponent />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.type(searchInput, 'test query');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/search is taking longer than expected/i)).toBeInTheDocument();
      }, { timeout: 10000 });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();
    });
  });

  describe('Flashcard Review Error Handling', () => {
    it('should handle card loading failures gracefully', async () => {
      errorSimulator.simulateNetworkFailure();

      render(
        <TestWrapper>
          <FlashcardReview />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/unable to load cards/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('should handle grading submission failures with retry', async () => {
      // Mock successful card loading but failed grading
      vi.mocked(api.getCards).mockResolvedValue([createMockCard()]);
      vi.mocked(api.gradeCard).mockRejectedValue(new Error('Network Error'));

      render(
        <TestWrapper>
          <FlashcardReview />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/front of card/i)).toBeInTheDocument();
      });

      const gradeButton = screen.getByRole('button', { name: /grade 4/i });
      await userEvent.click(gradeButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to save grade/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('should save progress locally when offline', async () => {
      errorSimulator.simulateNetworkFailure();

      // Mock successful initial load
      vi.mocked(api.getCards).mockResolvedValue([createMockCard()]);

      render(
        <TestWrapper>
          <FlashcardReview />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/front of card/i)).toBeInTheDocument();
      });

      const gradeButton = screen.getByRole('button', { name: /grade 4/i });
      await userEvent.click(gradeButton);

      await waitFor(() => {
        expect(screen.getByText(/saved locally/i)).toBeInTheDocument();
        expect(screen.getByText(/will sync when online/i)).toBeInTheDocument();
      });
    });
  });

  describe('Network Status and Offline Handling', () => {
    it('should show offline indicator when network is down', async () => {
      render(
        <TestWrapper>
          <OfflineIndicator />
        </TestWrapper>
      );

      // Simulate going offline
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(screen.getByText(/you are offline/i)).toBeInTheDocument();
      });
    });

    it('should show reconnection status when coming back online', async () => {
      render(
        <TestWrapper>
          <OfflineIndicator />
        </TestWrapper>
      );

      // Simulate going offline then online
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(screen.getByText(/you are offline/i)).toBeInTheDocument();
      });

      act(() => {
        window.dispatchEvent(new Event('online'));
      });

      await waitFor(() => {
        expect(screen.getByText(/reconnecting/i)).toBeInTheDocument();
      });
    });

    it('should queue operations when offline and sync when online', async () => {
      const mockSyncOperation = vi.fn();

      render(
        <TestWrapper>
          <FlashcardReview onOfflineOperation={mockSyncOperation} />
        </TestWrapper>
      );

      // Simulate offline state
      act(() => {
        window.dispatchEvent(new Event('offline'));
      });

      // Perform operation while offline
      const gradeButton = screen.getByRole('button', { name: /grade 4/i });
      await userEvent.click(gradeButton);

      // Come back online
      act(() => {
        window.dispatchEvent(new Event('online'));
      });

      await waitFor(() => {
        expect(mockSyncOperation).toHaveBeenCalled();
      });
    });
  });

  describe('Error Boundary Testing', () => {
    const ThrowError: React.FC<{ shouldThrow: boolean }> = ({ shouldThrow }) => {
      if (shouldThrow) {
        throw new Error('Test error');
      }
      return <div>No error</div>;
    };

    it('should catch JavaScript errors and show fallback UI', () => {
      render(
        <TestWrapper>
          <ThrowError shouldThrow={true} />
        </TestWrapper>
      );

      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reload page/i })).toBeInTheDocument();
    });

    it('should allow error recovery without full page reload', () => {
      const { rerender } = render(
        <TestWrapper>
          <ThrowError shouldThrow={true} />
        </TestWrapper>
      );

      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

      const retryButton = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryButton);

      rerender(
        <TestWrapper>
          <ThrowError shouldThrow={false} />
        </TestWrapper>
      );

      expect(screen.getByText(/no error/i)).toBeInTheDocument();
    });
  });

  describe('Input Validation and User Feedback', () => {
    it('should validate form inputs and show helpful messages', async () => {
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await userEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/please select a file/i)).toBeInTheDocument();
      });
    });

    it('should show loading states during operations', async () => {
      errorSimulator.simulateSlowNetwork(2000);

      render(
        <TestWrapper>
          <SearchComponent />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.type(searchInput, 'test query');
      await userEvent.keyboard('{Enter}');

      expect(screen.getByText(/searching/i)).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should provide contextual help for errors', async () => {
      errorSimulator.simulateServerError(413); // Payload too large

      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/upload document/i);
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      await userEvent.upload(fileInput, file);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await userEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/file is too large/i)).toBeInTheDocument();
        expect(screen.getByText(/try reducing the file size/i)).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /how to compress/i })).toBeInTheDocument();
      });
    });
  });

  describe('Performance Degradation Handling', () => {
    it('should show performance warnings for slow operations', async () => {
      errorSimulator.simulateSlowNetwork(8000); // 8 second delay

      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/upload document/i);
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      await userEvent.upload(fileInput, file);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await userEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/upload is taking longer than expected/i)).toBeInTheDocument();
      }, { timeout: 6000 });
    });

    it('should provide options to continue or cancel slow operations', async () => {
      errorSimulator.simulateSlowNetwork(10000);

      render(
        <TestWrapper>
          <SearchComponent />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.type(searchInput, 'test query');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /continue waiting/i })).toBeInTheDocument();
      }, { timeout: 6000 });
    });
  });

  describe('Accessibility Error Handling', () => {
    it('should announce errors to screen readers', async () => {
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await userEvent.click(uploadButton);

      await waitFor(() => {
        const errorMessage = screen.getByRole('alert');
        expect(errorMessage).toHaveTextContent(/please select a file/i);
      });
    });

    it('should maintain focus management during error states', async () => {
      render(
        <TestWrapper>
          <SearchComponent />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.click(searchInput);
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(document.activeElement).toBe(searchInput);
      });
    });
  });
});

// Integration tests for comprehensive error handling
describe('Comprehensive Error Handling Integration', () => {
  let errorSimulator: FrontendErrorSimulator;

  beforeEach(() => {
    errorSimulator = new FrontendErrorSimulator();
  });

  afterEach(() => {
    errorSimulator.restoreNetwork();
  });

  it('should handle multiple simultaneous errors gracefully', async () => {
    errorSimulator.simulateIntermittentFailure(0.8); // 80% failure rate

    render(
      <TestWrapper>
        <DocumentUpload />
        <SearchComponent />
        <FlashcardReview />
      </TestWrapper>
    );

    // Trigger multiple operations
    const fileInput = screen.getByLabelText(/upload document/i);
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    await userEvent.upload(fileInput, file);

    const searchInput = screen.getByPlaceholderText(/search/i);
    await userEvent.type(searchInput, 'test');

    // Should handle errors without crashing
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });

    // Application should remain functional
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('should maintain application state during error recovery', async () => {
    const { rerender } = render(
      <TestWrapper>
        <SearchComponent />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText(/search/i);
    await userEvent.type(searchInput, 'important query');

    // Simulate error
    errorSimulator.simulateNetworkFailure();
    await userEvent.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });

    // Restore network and retry
    errorSimulator.restoreNetwork();
    const retryButton = screen.getByRole('button', { name: /retry/i });
    await userEvent.click(retryButton);

    // Should maintain the search query
    expect(searchInput).toHaveValue('important query');
  });
});