/**
 * Error Notification Component Tests
 * Tests for the enhanced error notification component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorNotification from '../ErrorNotification';
import { ErrorNotificationState } from '../../lib/error-notification-manager';
import { NetworkErrorType, ClassifiedError } from '../../lib/error-handling';

// Mock error for testing
const createMockError = (type: NetworkErrorType = NetworkErrorType.CONNECTION_TIMEOUT): ClassifiedError => ({
  type,
  originalError: new Error('Test error'),
  statusCode: 408,
  isRetryable: true,
  userMessage: 'Test user message',
  technicalMessage: 'Test technical message',
  suggestedAction: 'Test suggested action',
  timestamp: new Date(),
  requestId: 'test-request-id'
});

const createMockNotification = (
  error: ClassifiedError,
  options: any = {}
): ErrorNotificationState => ({
  id: 'test-notification-id',
  error,
  options: {
    showRetryButton: true,
    showTechnicalDetails: false,
    ...options
  },
  timestamp: new Date(),
  dismissed: false,
  retryCount: 0
});

describe('ErrorNotification', () => {
  const mockOnRetry = jest.fn();
  const mockOnDismiss = jest.fn();
  const mockOnAction = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders error notification with basic information', () => {
    const error = createMockError();
    const notification = createMockNotification(error);

    render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    expect(screen.getByText(/Connection Timeout/)).toBeInTheDocument();
    expect(screen.getByText(/Test user message/)).toBeInTheDocument();
  });

  it('displays retry button when error is retryable', () => {
    const error = createMockError();
    const notification = createMockNotification(error, { showRetryButton: true });

    render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    const retryButton = screen.getByText(/Try Again/);
    expect(retryButton).toBeInTheDocument();

    fireEvent.click(retryButton);
    expect(mockOnRetry).toHaveBeenCalledWith('test-notification-id');
  });

  it('calls onDismiss when dismiss button is clicked', () => {
    const error = createMockError();
    const notification = createMockNotification(error);

    render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    const dismissButton = screen.getByLabelText('Dismiss notification');
    fireEvent.click(dismissButton);
    expect(mockOnDismiss).toHaveBeenCalledWith('test-notification-id');
  });

  it('shows technical details when enabled', () => {
    const error = createMockError();
    const notification = createMockNotification(error, { showTechnicalDetails: true });

    render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    const showDetailsButton = screen.getByText(/Show Details/);
    fireEvent.click(showDetailsButton);

    expect(screen.getByText(/Technical Details:/)).toBeInTheDocument();
    expect(screen.getByText(/CONNECTION_TIMEOUT/)).toBeInTheDocument();
    expect(screen.getByText(/test-request-id/)).toBeInTheDocument();
  });

  it('shows troubleshooting steps when available', () => {
    const error = createMockError();
    const notification = createMockNotification(error);

    render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    const troubleshootButton = screen.getByText(/Troubleshoot/);
    fireEvent.click(troubleshootButton);

    expect(screen.getByText(/Troubleshooting Steps:/)).toBeInTheDocument();
  });

  it('displays retry count when greater than 0', () => {
    const error = createMockError();
    const notification = createMockNotification(error);
    notification.retryCount = 2;

    render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    expect(screen.getByText(/Attempt #3/)).toBeInTheDocument();
  });

  it('applies correct severity styling', () => {
    const error = createMockError(NetworkErrorType.SERVER_ERROR);
    const notification = createMockNotification(error);

    const { container } = render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    // Check for high severity styling (red colors)
    const notificationElement = container.querySelector('.bg-red-50');
    expect(notificationElement).toBeInTheDocument();
  });

  it('handles different error types with appropriate icons', () => {
    const testCases = [
      { type: NetworkErrorType.CONNECTION_TIMEOUT, icon: '⏱️' },
      { type: NetworkErrorType.SERVER_ERROR, icon: '🔧' },
      { type: NetworkErrorType.NETWORK_UNREACHABLE, icon: '🌐' },
      { type: NetworkErrorType.RATE_LIMITED, icon: '⏳' }
    ];

    testCases.forEach(({ type, icon }) => {
      const error = createMockError(type);
      const notification = createMockNotification(error);

      const { unmount } = render(
        <ErrorNotification
          notification={notification}
          onRetry={mockOnRetry}
          onDismiss={mockOnDismiss}
          onAction={mockOnAction}
        />
      );

      const iconElement = screen.getByLabelText('Error icon');
      expect(iconElement).toHaveTextContent(icon);

      unmount();
    });
  });

  it('handles custom actions correctly', () => {
    const error = createMockError(NetworkErrorType.NETWORK_UNREACHABLE);
    const notification = createMockNotification(error);

    render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    // Look for "Check Network" button which should be available for network unreachable errors
    const checkNetworkButton = screen.getByText(/Check Network/);
    fireEvent.click(checkNetworkButton);

    expect(mockOnAction).toHaveBeenCalledWith('check_connection', 'test-notification-id');
  });

  it('shows support information for critical errors', () => {
    const error = createMockError(NetworkErrorType.CORS_ERROR);
    const notification = createMockNotification(error);

    render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    // CORS errors should show support information
    expect(screen.getByText(/Copy Debug Info/)).toBeInTheDocument();
  });

  it('handles context information correctly', () => {
    const error = createMockError();
    const notification = createMockNotification(error, {
      context: {
        operation: 'file_upload',
        resource: 'test-file.pdf',
        userAction: 'upload_file'
      },
      showTechnicalDetails: true
    });

    render(
      <ErrorNotification
        notification={notification}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        onAction={mockOnAction}
      />
    );

    // Should show context-specific title
    expect(screen.getByText(/Connection Timeout During File Upload/)).toBeInTheDocument();
  });
});