import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../../test/utils';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { SearchInput } from '../SearchInput';

describe('SearchInput', () => {
  const mockOnQueryChange = vi.fn();
  const mockOnSearch = vi.fn();
  const mockOnShowSuggestions = vi.fn();

  const defaultProps = {
    query: '',
    onQueryChange: mockOnQueryChange,
    onSearch: mockOnSearch,
    suggestions: [],
    showSuggestions: false,
    onShowSuggestions: mockOnShowSuggestions,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders search input with default placeholder', () => {
      render(<SearchInput {...defaultProps} />);

      const input = screen.getByRole('combobox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('placeholder', 'Search knowledge points and flashcards...');
    });

    it('renders with custom placeholder', () => {
      render(<SearchInput {...defaultProps} placeholder="Custom placeholder" />);

      const input = screen.getByRole('combobox');
      expect(input).toHaveAttribute('placeholder', 'Custom placeholder');
    });

    it('renders search button', () => {
      render(<SearchInput {...defaultProps} />);

      expect(screen.getByRole('button', { name: 'Search' })).toBeInTheDocument();
    });

    it('renders search icon', () => {
      render(<SearchInput {...defaultProps} />);

      const searchIcon = screen.getByRole('combobox').parentElement?.querySelector('svg');
      expect(searchIcon).toBeInTheDocument();
    });
  });

  describe('Input Interaction', () => {
    it('calls onQueryChange when typing', async () => {
      const user = userEvent.setup();
      render(<SearchInput {...defaultProps} />);

      const input = screen.getByRole('combobox');
      await user.type(input, 'machine learning');

      expect(mockOnQueryChange).toHaveBeenCalledTimes(16); // Each character
      expect(mockOnQueryChange).toHaveBeenLastCalledWith('machine learning');
    });

    it('displays current query value', () => {
      render(<SearchInput {...defaultProps} query="test query" />);

      const input = screen.getByRole('combobox') as HTMLInputElement;
      expect(input.value).toBe('test query');
    });

    it('calls onSearch when Enter is pressed', async () => {
      const user = userEvent.setup();
      render(<SearchInput {...defaultProps} query="test" />);

      const input = screen.getByRole('combobox');
      await user.type(input, '{Enter}');

      expect(mockOnSearch).toHaveBeenCalled();
      expect(mockOnShowSuggestions).toHaveBeenCalledWith(false);
    });

    it('calls onSearch when search button is clicked', async () => {
      const user = userEvent.setup();
      render(<SearchInput {...defaultProps} query="test" />);

      const searchButton = screen.getByRole('button', { name: 'Search' });
      await user.click(searchButton);

      expect(mockOnSearch).toHaveBeenCalled();
    });
  });

  describe('Clear Functionality', () => {
    it('shows clear button when query is not empty', () => {
      render(<SearchInput {...defaultProps} query="test query" />);

      expect(screen.getByRole('button', { name: 'Clear search' })).toBeInTheDocument();
    });

    it('does not show clear button when query is empty', () => {
      render(<SearchInput {...defaultProps} query="" />);

      expect(screen.queryByRole('button', { name: 'Clear search' })).not.toBeInTheDocument();
    });

    it('clears query when clear button is clicked', async () => {
      const user = userEvent.setup();
      render(<SearchInput {...defaultProps} query="test query" />);

      const clearButton = screen.getByRole('button', { name: 'Clear search' });
      await user.click(clearButton);

      expect(mockOnQueryChange).toHaveBeenCalledWith('');
      expect(mockOnShowSuggestions).toHaveBeenCalledWith(false);
    });
  });

  describe('Suggestions', () => {
    const mockSuggestions = ['machine learning', 'neural networks', 'deep learning'];

    it('shows suggestions when showSuggestions is true', () => {
      render(
        <SearchInput
          {...defaultProps}
          suggestions={mockSuggestions}
          showSuggestions={true}
        />
      );

      expect(screen.getByRole('listbox')).toBeInTheDocument();
      mockSuggestions.forEach(suggestion => {
        expect(screen.getByText(suggestion)).toBeInTheDocument();
      });
    });

    it('does not show suggestions when showSuggestions is false', () => {
      render(
        <SearchInput
          {...defaultProps}
          suggestions={mockSuggestions}
          showSuggestions={false}
        />
      );

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('calls onQueryChange when suggestion is clicked', async () => {
      const user = userEvent.setup();
      render(
        <SearchInput
          {...defaultProps}
          suggestions={mockSuggestions}
          showSuggestions={true}
        />
      );

      const suggestion = screen.getByText('machine learning');
      await user.click(suggestion);

      expect(mockOnQueryChange).toHaveBeenCalledWith('machine learning');
      expect(mockOnShowSuggestions).toHaveBeenCalledWith(false);
    });

    it('shows suggestions when input is focused and suggestions exist', async () => {
      const user = userEvent.setup();
      render(
        <SearchInput
          {...defaultProps}
          suggestions={mockSuggestions}
          showSuggestions={false}
        />
      );

      const input = screen.getByRole('combobox');
      await user.click(input);

      expect(mockOnShowSuggestions).toHaveBeenCalledWith(true);
    });
  });

  describe('Keyboard Navigation', () => {
    const mockSuggestions = ['machine learning', 'neural networks', 'deep learning'];

    it('navigates to first suggestion with ArrowDown', async () => {
      const user = userEvent.setup();
      render(
        <SearchInput
          {...defaultProps}
          suggestions={mockSuggestions}
          showSuggestions={true}
        />
      );

      const input = screen.getByRole('combobox');
      await user.type(input, '{ArrowDown}');

      const firstSuggestion = screen.getByRole('option', { name: /machine learning/ });
      expect(firstSuggestion).toHaveFocus();
    });

    it('closes suggestions with Escape key', async () => {
      const user = userEvent.setup();
      render(
        <SearchInput
          {...defaultProps}
          suggestions={mockSuggestions}
          showSuggestions={true}
        />
      );

      const input = screen.getByRole('combobox');
      await user.type(input, '{Escape}');

      expect(mockOnShowSuggestions).toHaveBeenCalledWith(false);
    });

    it('selects suggestion with Enter key', async () => {
      const user = userEvent.setup();
      render(
        <SearchInput
          {...defaultProps}
          suggestions={mockSuggestions}
          showSuggestions={true}
        />
      );

      // Navigate to first suggestion
      const input = screen.getByRole('combobox');
      await user.type(input, '{ArrowDown}');

      const firstSuggestion = screen.getByRole('option', { name: /machine learning/ });
      await user.type(firstSuggestion, '{Enter}');

      expect(mockOnQueryChange).toHaveBeenCalledWith('machine learning');
      expect(mockOnSearch).toHaveBeenCalled();
    });

    it('navigates between suggestions with arrow keys', async () => {
      const user = userEvent.setup();
      render(
        <SearchInput
          {...defaultProps}
          suggestions={mockSuggestions}
          showSuggestions={true}
        />
      );

      // Navigate to first suggestion
      const input = screen.getByRole('combobox');
      await user.type(input, '{ArrowDown}');

      const firstSuggestion = screen.getByRole('option', { name: /machine learning/ });
      expect(firstSuggestion).toHaveFocus();

      // Navigate to second suggestion
      await user.type(firstSuggestion, '{ArrowDown}');

      const secondSuggestion = screen.getByRole('option', { name: /neural networks/ });
      expect(secondSuggestion).toHaveFocus();

      // Navigate back to first
      await user.type(secondSuggestion, '{ArrowUp}');
      expect(firstSuggestion).toHaveFocus();
    });
  });

  describe('Loading State', () => {
    it('disables input when searching', () => {
      render(<SearchInput {...defaultProps} isSearching={true} />);

      const input = screen.getByRole('combobox');
      expect(input).toBeDisabled();
    });

    it('disables search button when searching', () => {
      render(<SearchInput {...defaultProps} isSearching={true} />);

      const searchButton = screen.getByRole('button', { name: /Search/ });
      expect(searchButton).toBeDisabled();
    });

    it('shows loading spinner when searching', () => {
      render(<SearchInput {...defaultProps} isSearching={true} />);

      const spinner = screen.getByRole('button', { name: /Search/ }).querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('disables search button when query is empty', () => {
      render(<SearchInput {...defaultProps} query="" />);

      const searchButton = screen.getByRole('button', { name: 'Search' });
      expect(searchButton).toBeDisabled();
    });

    it('disables search button when query is only whitespace', () => {
      render(<SearchInput {...defaultProps} query="   " />);

      const searchButton = screen.getByRole('button', { name: 'Search' });
      expect(searchButton).toBeDisabled();
    });
  });

  describe('Click Outside', () => {
    it('closes suggestions when clicking outside', async () => {
      const user = userEvent.setup();
      render(
        <div>
          <SearchInput
            {...defaultProps}
            suggestions={['test']}
            showSuggestions={true}
          />
          <div data-testid="outside">Outside element</div>
        </div>
      );

      const outsideElement = screen.getByTestId('outside');
      await user.click(outsideElement);

      expect(mockOnShowSuggestions).toHaveBeenCalledWith(false);
    });

    it('does not close suggestions when clicking inside', async () => {
      const user = userEvent.setup();
      render(
        <SearchInput
          {...defaultProps}
          suggestions={['test']}
          showSuggestions={true}
        />
      );

      const input = screen.getByRole('combobox');
      await user.click(input);

      // Should not call onShowSuggestions(false) when clicking inside
      expect(mockOnShowSuggestions).not.toHaveBeenCalledWith(false);
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<SearchInput {...defaultProps} />);

      const input = screen.getByRole('combobox');
      expect(input).toHaveAttribute('aria-label', 'Search input');
      expect(input).toHaveAttribute('aria-expanded', 'false');
      expect(input).toHaveAttribute('aria-haspopup', 'listbox');
      expect(input).toHaveAttribute('role', 'combobox');
      expect(input).toHaveAttribute('autoComplete', 'off');
    });

    it('updates aria-expanded when suggestions are shown', () => {
      render(
        <SearchInput
          {...defaultProps}
          suggestions={['test']}
          showSuggestions={true}
        />
      );

      const input = screen.getByRole('combobox');
      expect(input).toHaveAttribute('aria-expanded', 'true');
    });

    it('has proper listbox attributes', () => {
      render(
        <SearchInput
          {...defaultProps}
          suggestions={['test']}
          showSuggestions={true}
        />
      );

      const listbox = screen.getByRole('listbox');
      expect(listbox).toHaveAttribute('aria-label', 'Search suggestions');
    });

    it('has proper option attributes', () => {
      render(
        <SearchInput
          {...defaultProps}
          suggestions={['machine learning']}
          showSuggestions={true}
        />
      );

      const option = screen.getByRole('option');
      expect(option).toHaveAttribute('role', 'option');
      expect(option).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      render(<SearchInput {...defaultProps} className="custom-class" />);

      const container = screen.getByRole('combobox').closest('.custom-class');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty suggestions array', () => {
      render(
        <SearchInput
          {...defaultProps}
          suggestions={[]}
          showSuggestions={true}
        />
      );

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('handles undefined suggestions', () => {
      render(
        <SearchInput
          {...defaultProps}
          suggestions={undefined as any}
          showSuggestions={true}
        />
      );

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('prevents default on Enter key', async () => {
      const user = userEvent.setup();
      const mockPreventDefault = vi.fn();
      
      render(<SearchInput {...defaultProps} query="test" />);

      const input = screen.getByRole('combobox');
      
      // Mock the event
      const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' });
      enterEvent.preventDefault = mockPreventDefault;
      
      fireEvent.keyDown(input, enterEvent);

      expect(mockOnSearch).toHaveBeenCalled();
    });
  });
});