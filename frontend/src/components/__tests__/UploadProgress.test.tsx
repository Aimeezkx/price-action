/**
 * Upload Progress Component Tests
 * Tests for the upload progress component with various states
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import UploadProgress from '../UploadProgress';
import { UploadStatus } from '../UploadProgress';

describe('UploadProgress', () => {
  const mockOnCancel = jest.fn();
  const mockOnRetry = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders upload progress with basic information', () => {
    render(
      <UploadProgress
        status="uploading"
        progress={50}
        fileName="test-document.pdf"
        fileSize={1024 * 1024} // 1MB
        onCancel={mockOnCancel}
        onRetry={mockOnRetry}
      />
    );

    expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    expect(screen.getByText('1 MB')).toBeInTheDocument();
    expect(screen.getByText('50% complete')).toBeInTheDocument();
    expect(screen.getByText('Uploading...')).toBeInTheDocument();
  });

  it('shows upload speed and time remaining when provided', () => {
    render(
      <UploadProgress
        status="uploading"
        progress={30}
        fileName="test-document.pdf"
        uploadSpeed={1024 * 100} // 100 KB/s
        timeRemaining={60} // 1 minute
        onCancel={mockOnCancel}
        onRetry={mockOnRetry}
      />
    );

    expect(screen.getByText(/100 KB\/s/)).toBeInTheDocument();
    expect(screen.getByText(/1m 0s remaining/)).toBeInTheDocument();
  });

  it('displays success state correctly', () => {
    render(
      <UploadProgress
        status="success"
        progress={100}
        fileName="test-document.pdf"
        onCancel={mockOnCancel}
        onRetry={mockOnRetry}
      />
    );

    expect(screen.getByText('Upload completed successfully')).toBeInTheDocument();
    expect(screen.getByText('✓ Upload successful')).toBeInTheDocument();
    expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
    expect(screen.queryByText('Retry Upload')).not.toBeInTheDocument();
  });

  it('displays failed state with retry button', () => {
    render(
      <UploadProgress
        status="failed"
        progress={75}
        fileName="test-document.pdf"
        error="Network connection failed"
        onCancel={mockOnCancel}
        onRetry={mockOnRetry}
      />
    );

    expect(screen.getByText('Network connection failed')).toBeInTheDocument();
    expect(screen.getByText('Retry Upload')).toBeInTheDocument();
    expect(screen.queryByText('Cancel')).not.toBeInTheDocument();

    const retryButton = screen.getByText('Retry Upload');
    fireEvent.click(retryButton);
    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it('shows cancel button during active upload', () => {
    render(
      <UploadProgress
        status="uploading"
        progress={25}
        fileName="test-document.pdf"
        onCancel={mockOnCancel}
        onRetry={mockOnRetry}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    expect(cancelButton).toBeInTheDocument();

    fireEvent.click(cancelButton);
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('displays processing state correctly', () => {
    render(
      <UploadProgress
        status="processing"
        progress={100}
        fileName="test-document.pdf"
        onCancel={mockOnCancel}
        onRetry={mockOnRetry}
      />
    );

    expect(screen.getByText('Processing document...')).toBeInTheDocument();
    expect(screen.getByText('100% complete')).toBeInTheDocument();
  });

  it('displays cancelled state correctly', () => {
    render(
      <UploadProgress
        status="cancelled"
        progress={40}
        fileName="test-document.pdf"
        onCancel={mockOnCancel}
        onRetry={mockOnRetry}
      />
    );

    expect(screen.getByText('Upload cancelled')).toBeInTheDocument();
    expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
    expect(screen.queryByText('Retry Upload')).not.toBeInTheDocument();
  });

  it('formats file sizes correctly', () => {
    const testCases = [
      { size: 1024, expected: '1 KB' },
      { size: 1024 * 1024, expected: '1 MB' },
      { size: 1024 * 1024 * 1024, expected: '1 GB' },
      { size: 1536, expected: '1.5 KB' }
    ];

    testCases.forEach(({ size, expected }) => {
      const { unmount } = render(
        <UploadProgress
          status="uploading"
          progress={50}
          fileName="test-document.pdf"
          fileSize={size}
          onCancel={mockOnCancel}
          onRetry={mockOnRetry}
        />
      );

      expect(screen.getByText(expected)).toBeInTheDocument();
      unmount();
    });
  });

  it('formats time remaining correctly', () => {
    const testCases = [
      { seconds: 30, expected: '30s' },
      { seconds: 90, expected: '1m 30s' },
      { seconds: 3661, expected: '61m 1s' }
    ];

    testCases.forEach(({ seconds, expected }) => {
      const { unmount } = render(
        <UploadProgress
          status="uploading"
          progress={50}
          fileName="test-document.pdf"
          timeRemaining={seconds}
          onCancel={mockOnCancel}
          onRetry={mockOnRetry}
        />
      );

      expect(screen.getByText(new RegExp(expected))).toBeInTheDocument();
      unmount();
    });
  });

  it('applies correct progress bar colors for different states', () => {
    const testCases: Array<{ status: UploadStatus; colorClass: string }> = [
      { status: 'uploading', colorClass: 'bg-blue-500' },
      { status: 'processing', colorClass: 'bg-yellow-500' },
      { status: 'success', colorClass: 'bg-green-500' },
      { status: 'failed', colorClass: 'bg-red-500' },
      { status: 'cancelled', colorClass: 'bg-gray-500' }
    ];

    testCases.forEach(({ status, colorClass }) => {
      const { container, unmount } = render(
        <UploadProgress
          status={status}
          progress={50}
          fileName="test-document.pdf"
          onCancel={mockOnCancel}
          onRetry={mockOnRetry}
        />
      );

      const progressBar = container.querySelector(`.${colorClass}`);
      expect(progressBar).toBeInTheDocument();
      unmount();
    });
  });

  it('handles edge cases for progress values', () => {
    const testCases = [
      { progress: -10, expected: '0%' },
      { progress: 0, expected: '0%' },
      { progress: 50, expected: '50%' },
      { progress: 100, expected: '100%' },
      { progress: 150, expected: '100%' }
    ];

    testCases.forEach(({ progress, expected }) => {
      const { unmount } = render(
        <UploadProgress
          status="uploading"
          progress={progress}
          fileName="test-document.pdf"
          onCancel={mockOnCancel}
          onRetry={mockOnRetry}
        />
      );

      expect(screen.getByText(`${expected} complete`)).toBeInTheDocument();
      unmount();
    });
  });

  it('does not show cancel button when onCancel is not provided', () => {
    render(
      <UploadProgress
        status="uploading"
        progress={50}
        fileName="test-document.pdf"
        onRetry={mockOnRetry}
      />
    );

    expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
  });

  it('does not show retry button when onRetry is not provided', () => {
    render(
      <UploadProgress
        status="failed"
        progress={50}
        fileName="test-document.pdf"
        error="Upload failed"
        onCancel={mockOnCancel}
      />
    );

    expect(screen.queryByText('Retry Upload')).not.toBeInTheDocument();
  });
});