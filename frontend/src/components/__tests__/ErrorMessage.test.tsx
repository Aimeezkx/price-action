import React from 'react';
import { render, screen, fireEvent } from '../../../test/utils';
import { vi } from 'vitest';
import { ErrorMessage } from '../ErrorMessage';

describe('ErrorMessage', () => {
  const mockOnRetry = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders error message correctly', () => {
      render(<ErrorMessage message="Something went wrong" />);

      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('renders error icon', () => {
      render(<ErrorMessage message="Test error" />);

      const errorIcon = screen.getByRole('img', { hidden: true });
      expect(errorIcon).toBeInTheDocument();
      expect(errorIcon).toHaveClass('text-red-400');
    });

    it('applies correct styling classes', () => {
      render(<ErrorMessage message="Test error" />);

      const container = screen.getByText('Something went wrong').closest('div');
      expect(container).toHaveClass('bg-red-50');
    });
  });

  describe('Retry Functionality', () => {
    it('shows retry button when onRetry is provided', () => {
      render(<ErrorMessage message="Test error" onRetry={mockOnRetry} />);

      expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
    });

    it('does not show retry button when onRetry is not provided', () => {
      render(<ErrorMessage message="Test error" />);

      expect(screen.queryByRole('button', { name: 'Try again' })).not.toBeInTheDocument();
    });

    it('calls onRetry when retry button is clicked', () => {
      render(<ErrorMessage message="Test error" onRetry={mockOnRetry} />);

      const retryButton = screen.getByRole('button', { name: 'Try again' });
      fireEvent.click(retryButton);

      expect(mockOnRetry).toHaveBeenCalledTimes(1);
    });

    it('retry button has correct styling', () => {
      render(<ErrorMessage message="Test error" onRetry={mockOnRetry} />);

      const retryButton = screen.getByRole('button', { name: 'Try again' });
      expect(retryButton).toHaveClass('bg-red-100', 'text-red-800', 'hover:bg-red-200');
    });
  });

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      render(<ErrorMessage message="Test error" onRetry={mockOnRetry} />);

      expect(screen.getByRole('heading', { name: 'Error' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
    });

    it('retry button is focusable', () => {
      render(<ErrorMessage message="Test error" onRetry={mockOnRetry} />);

      const retryButton = screen.getByRole('button', { name: 'Try again' });
      expect(retryButton).toHaveAttribute('type', 'button');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty message', () => {
      render(<ErrorMessage message="" />);

      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('')).toBeInTheDocument();
    });

    it('handles long error messages', () => {
      const longMessage = 'This is a very long error message that should still be displayed correctly even when it contains a lot of text and might wrap to multiple lines.';
      
      render(<ErrorMessage message={longMessage} />);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('handles special characters in message', () => {
      const messageWithSpecialChars = 'Error: <script>alert("test")</script> & other chars';
      
      render(<ErrorMessage message={messageWithSpecialChars} />);

      expect(screen.getByText(messageWithSpecialChars)).toBeInTheDocument();
    });
  });

  describe('Multiple Clicks', () => {
    it('handles multiple rapid clicks on retry button', () => {
      render(<ErrorMessage message="Test error" onRetry={mockOnRetry} />);

      const retryButton = screen.getByRole('button', { name: 'Try again' });
      
      // Click multiple times rapidly
      fireEvent.click(retryButton);
      fireEvent.click(retryButton);
      fireEvent.click(retryButton);

      expect(mockOnRetry).toHaveBeenCalledTimes(3);
    });
  });
});