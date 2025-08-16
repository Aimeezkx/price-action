import React from 'react';
import { render, screen, fireEvent } from '../../../test/utils';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { GradingInterface } from '../GradingInterface';

describe('GradingInterface', () => {
  const mockOnGrade = vi.fn();

  const defaultProps = {
    onGrade: mockOnGrade,
    disabled: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders all grade buttons', () => {
      render(<GradingInterface {...defaultProps} />);

      expect(screen.getByRole('button', { name: /again/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /hard/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /good/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /easy/i })).toBeInTheDocument();
    });

    it('renders grade descriptions', () => {
      render(<GradingInterface {...defaultProps} />);

      expect(screen.getByText('< 1 min')).toBeInTheDocument();
      expect(screen.getByText('< 6 min')).toBeInTheDocument();
      expect(screen.getByText('< 10 min')).toBeInTheDocument();
      expect(screen.getByText('4 days')).toBeInTheDocument();
    });

    it('renders keyboard shortcuts', () => {
      render(<GradingInterface {...defaultProps} />);

      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
    });
  });

  describe('Grade Selection', () => {
    it('calls onGrade with correct value when Again button is clicked', async () => {
      const user = userEvent.setup();
      render(<GradingInterface {...defaultProps} />);

      const againButton = screen.getByRole('button', { name: /again/i });
      await user.click(againButton);

      expect(mockOnGrade).toHaveBeenCalledWith(1);
    });

    it('calls onGrade with correct value when Hard button is clicked', async () => {
      const user = userEvent.setup();
      render(<GradingInterface {...defaultProps} />);

      const hardButton = screen.getByRole('button', { name: /hard/i });
      await user.click(hardButton);

      expect(mockOnGrade).toHaveBeenCalledWith(2);
    });

    it('calls onGrade with correct value when Good button is clicked', async () => {
      const user = userEvent.setup();
      render(<GradingInterface {...defaultProps} />);

      const goodButton = screen.getByRole('button', { name: /good/i });
      await user.click(goodButton);

      expect(mockOnGrade).toHaveBeenCalledWith(3);
    });

    it('calls onGrade with correct value when Easy button is clicked', async () => {
      const user = userEvent.setup();
      render(<GradingInterface {...defaultProps} />);

      const easyButton = screen.getByRole('button', { name: /easy/i });
      await user.click(easyButton);

      expect(mockOnGrade).toHaveBeenCalledWith(4);
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('handles keyboard shortcut 1 for Again', () => {
      render(<GradingInterface {...defaultProps} />);

      fireEvent.keyDown(document, { key: '1' });

      expect(mockOnGrade).toHaveBeenCalledWith(1);
    });

    it('handles keyboard shortcut 2 for Hard', () => {
      render(<GradingInterface {...defaultProps} />);

      fireEvent.keyDown(document, { key: '2' });

      expect(mockOnGrade).toHaveBeenCalledWith(2);
    });

    it('handles keyboard shortcut 3 for Good', () => {
      render(<GradingInterface {...defaultProps} />);

      fireEvent.keyDown(document, { key: '3' });

      expect(mockOnGrade).toHaveBeenCalledWith(3);
    });

    it('handles keyboard shortcut 4 for Easy', () => {
      render(<GradingInterface {...defaultProps} />);

      fireEvent.keyDown(document, { key: '4' });

      expect(mockOnGrade).toHaveBeenCalledWith(4);
    });

    it('ignores other keyboard inputs', () => {
      render(<GradingInterface {...defaultProps} />);

      fireEvent.keyDown(document, { key: '5' });
      fireEvent.keyDown(document, { key: 'a' });
      fireEvent.keyDown(document, { key: 'Enter' });

      expect(mockOnGrade).not.toHaveBeenCalled();
    });

    it('does not handle keyboard shortcuts when disabled', () => {
      render(<GradingInterface {...defaultProps} disabled={true} />);

      fireEvent.keyDown(document, { key: '1' });

      expect(mockOnGrade).not.toHaveBeenCalled();
    });
  });

  describe('Disabled State', () => {
    it('disables all buttons when disabled prop is true', () => {
      render(<GradingInterface {...defaultProps} disabled={true} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toBeDisabled();
      });
    });

    it('applies disabled styling when disabled', () => {
      render(<GradingInterface {...defaultProps} disabled={true} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('opacity-50', 'cursor-not-allowed');
      });
    });

    it('does not call onGrade when disabled button is clicked', async () => {
      const user = userEvent.setup();
      render(<GradingInterface {...defaultProps} disabled={true} />);

      const againButton = screen.getByRole('button', { name: /again/i });
      await user.click(againButton);

      expect(mockOnGrade).not.toHaveBeenCalled();
    });
  });

  describe('Visual Styling', () => {
    it('applies correct color classes to buttons', () => {
      render(<GradingInterface {...defaultProps} />);

      const againButton = screen.getByRole('button', { name: /again/i });
      const hardButton = screen.getByRole('button', { name: /hard/i });
      const goodButton = screen.getByRole('button', { name: /good/i });
      const easyButton = screen.getByRole('button', { name: /easy/i });

      expect(againButton).toHaveClass('bg-red-500', 'hover:bg-red-600');
      expect(hardButton).toHaveClass('bg-orange-500', 'hover:bg-orange-600');
      expect(goodButton).toHaveClass('bg-green-500', 'hover:bg-green-600');
      expect(easyButton).toHaveClass('bg-blue-500', 'hover:bg-blue-600');
    });

    it('has proper button structure and content', () => {
      render(<GradingInterface {...defaultProps} />);

      const againButton = screen.getByRole('button', { name: /again/i });
      
      // Check that button contains both text and keyboard shortcut
      expect(againButton).toHaveTextContent('Again');
      expect(againButton).toHaveTextContent('1');
      expect(againButton).toHaveTextContent('< 1 min');
    });
  });

  describe('Accessibility', () => {
    it('has proper button roles', () => {
      render(<GradingInterface {...defaultProps} />);

      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(4);
    });

    it('has accessible button names', () => {
      render(<GradingInterface {...defaultProps} />);

      expect(screen.getByRole('button', { name: /again/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /hard/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /good/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /easy/i })).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<GradingInterface {...defaultProps} />);

      const againButton = screen.getByRole('button', { name: /again/i });
      
      await user.tab();
      expect(againButton).toHaveFocus();

      await user.tab();
      const hardButton = screen.getByRole('button', { name: /hard/i });
      expect(hardButton).toHaveFocus();
    });

    it('supports Enter key activation', async () => {
      const user = userEvent.setup();
      render(<GradingInterface {...defaultProps} />);

      const againButton = screen.getByRole('button', { name: /again/i });
      againButton.focus();
      
      await user.keyboard('{Enter}');

      expect(mockOnGrade).toHaveBeenCalledWith(1);
    });

    it('supports Space key activation', async () => {
      const user = userEvent.setup();
      render(<GradingInterface {...defaultProps} />);

      const againButton = screen.getByRole('button', { name: /again/i });
      againButton.focus();
      
      await user.keyboard(' ');

      expect(mockOnGrade).toHaveBeenCalledWith(1);
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className when provided', () => {
      render(<GradingInterface {...defaultProps} className="custom-class" />);

      const container = screen.getByRole('button', { name: /again/i }).closest('.custom-class');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Event Cleanup', () => {
    it('removes keyboard event listeners on unmount', () => {
      const addEventListenerSpy = vi.spyOn(document, 'addEventListener');
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');

      const { unmount } = render(<GradingInterface {...defaultProps} />);

      expect(addEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));

      addEventListenerSpy.mockRestore();
      removeEventListenerSpy.mockRestore();
    });
  });

  describe('Multiple Instances', () => {
    it('handles multiple grading interfaces independently', async () => {
      const mockOnGrade1 = vi.fn();
      const mockOnGrade2 = vi.fn();
      const user = userEvent.setup();

      render(
        <div>
          <GradingInterface onGrade={mockOnGrade1} />
          <GradingInterface onGrade={mockOnGrade2} />
        </div>
      );

      const againButtons = screen.getAllByRole('button', { name: /again/i });
      
      await user.click(againButtons[0]);
      expect(mockOnGrade1).toHaveBeenCalledWith(1);
      expect(mockOnGrade2).not.toHaveBeenCalled();

      vi.clearAllMocks();

      await user.click(againButtons[1]);
      expect(mockOnGrade2).toHaveBeenCalledWith(1);
      expect(mockOnGrade1).not.toHaveBeenCalled();
    });
  });

  describe('Performance', () => {
    it('does not re-render unnecessarily', () => {
      const renderSpy = vi.fn();
      
      const TestComponent = (props: any) => {
        renderSpy();
        return <GradingInterface {...props} />;
      };

      const { rerender } = render(<TestComponent {...defaultProps} />);
      
      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render with same props
      rerender(<TestComponent {...defaultProps} />);
      
      expect(renderSpy).toHaveBeenCalledTimes(2);
    });
  });
});