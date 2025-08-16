import React from 'react';
import { render, screen } from '../../../test/utils';
import { LoadingSpinner } from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  describe('Basic Rendering', () => {
    it('renders spinner with default size', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass('h-8', 'w-8'); // Default md size
    });

    it('has spinning animation', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('animate-spin');
    });

    it('has correct border styling', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('rounded-full', 'border-2', 'border-gray-300', 'border-t-blue-600');
    });
  });

  describe('Size Variants', () => {
    it('renders small size correctly', () => {
      render(<LoadingSpinner size="sm" />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('h-4', 'w-4');
    });

    it('renders medium size correctly', () => {
      render(<LoadingSpinner size="md" />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('h-8', 'w-8');
    });

    it('renders large size correctly', () => {
      render(<LoadingSpinner size="lg" />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('h-12', 'w-12');
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      render(<LoadingSpinner className="custom-class" />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('custom-class');
    });

    it('combines custom className with default classes', () => {
      render(<LoadingSpinner className="text-red-500" />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('animate-spin', 'text-red-500');
    });

    it('applies custom className with different sizes', () => {
      render(<LoadingSpinner size="lg" className="border-red-500" />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('h-12', 'w-12', 'border-red-500');
    });
  });

  describe('Accessibility', () => {
    it('has implicit loading role', () => {
      render(<LoadingSpinner />);

      // The div should be identifiable as a loading indicator
      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toBeInTheDocument();
    });

    it('is not focusable', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).not.toHaveAttribute('tabIndex');
    });
  });

  describe('Performance', () => {
    it('renders quickly with minimal DOM elements', () => {
      const { container } = render(<LoadingSpinner />);

      // Should only create one div element
      expect(container.children).toHaveLength(1);
      expect(container.firstChild?.nodeName).toBe('DIV');
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined size gracefully', () => {
      render(<LoadingSpinner size={undefined} />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('h-8', 'w-8'); // Should default to md
    });

    it('handles empty className', () => {
      render(<LoadingSpinner className="" />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('animate-spin');
    });

    it('handles null className', () => {
      render(<LoadingSpinner className={null as any} />);

      const spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('animate-spin');
    });
  });

  describe('Visual Consistency', () => {
    it('maintains consistent border width across sizes', () => {
      const { rerender } = render(<LoadingSpinner size="sm" />);
      let spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('border-2');

      rerender(<LoadingSpinner size="md" />);
      spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('border-2');

      rerender(<LoadingSpinner size="lg" />);
      spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('border-2');
    });

    it('maintains consistent color scheme across sizes', () => {
      const { rerender } = render(<LoadingSpinner size="sm" />);
      let spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('border-gray-300', 'border-t-blue-600');

      rerender(<LoadingSpinner size="md" />);
      spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('border-gray-300', 'border-t-blue-600');

      rerender(<LoadingSpinner size="lg" />);
      spinner = screen.getByRole('status', { hidden: true });
      expect(spinner).toHaveClass('border-gray-300', 'border-t-blue-600');
    });
  });
});