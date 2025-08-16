import React from 'react';
import { render, screen, fireEvent } from '../../../test/utils';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { CardFilters } from '../CardFilters';

describe('CardFilters', () => {
  const mockOnFiltersChange = vi.fn();
  const mockChapters = [
    { id: 'chapter-1', title: 'Introduction to Machine Learning' },
    { id: 'chapter-2', title: 'Neural Networks' },
    { id: 'chapter-3', title: 'Deep Learning' },
  ];

  const defaultProps = {
    filters: {},
    onFiltersChange: mockOnFiltersChange,
    chapters: mockChapters,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders all filter controls', () => {
      render(<CardFilters {...defaultProps} />);

      expect(screen.getByLabelText('Chapter')).toBeInTheDocument();
      expect(screen.getByLabelText('Difficulty')).toBeInTheDocument();
      expect(screen.getByLabelText('Card Type')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Clear All' })).toBeInTheDocument();
    });

    it('renders chapter options correctly', () => {
      render(<CardFilters {...defaultProps} />);

      const chapterSelect = screen.getByLabelText('Chapter');
      expect(chapterSelect).toBeInTheDocument();
      
      // Check default option
      expect(screen.getByRole('option', { name: 'All Chapters' })).toBeInTheDocument();
      
      // Check chapter options
      mockChapters.forEach(chapter => {
        expect(screen.getByRole('option', { name: chapter.title })).toBeInTheDocument();
      });
    });

    it('renders difficulty options correctly', () => {
      render(<CardFilters {...defaultProps} />);

      expect(screen.getByRole('option', { name: 'All Difficulties' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Easy (≤1.5)' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Medium (1.5-2.5)' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Hard (>2.5)' })).toBeInTheDocument();
    });

    it('renders card type options correctly', () => {
      render(<CardFilters {...defaultProps} />);

      expect(screen.getByRole('option', { name: 'All Types' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Q&A Cards' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Cloze Deletion' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Image Hotspot' })).toBeInTheDocument();
    });
  });

  describe('Filter Selection', () => {
    it('calls onFiltersChange when chapter is selected', async () => {
      const user = userEvent.setup();
      render(<CardFilters {...defaultProps} />);

      const chapterSelect = screen.getByLabelText('Chapter');
      await user.selectOptions(chapterSelect, 'chapter-1');

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        chapter: 'chapter-1',
      });
    });

    it('calls onFiltersChange when difficulty is selected', async () => {
      const user = userEvent.setup();
      render(<CardFilters {...defaultProps} />);

      const difficultySelect = screen.getByLabelText('Difficulty');
      await user.selectOptions(difficultySelect, 'easy');

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        difficulty: 'easy',
      });
    });

    it('calls onFiltersChange when card type is selected', async () => {
      const user = userEvent.setup();
      render(<CardFilters {...defaultProps} />);

      const cardTypeSelect = screen.getByLabelText('Card Type');
      await user.selectOptions(cardTypeSelect, 'qa');

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        cardType: 'qa',
      });
    });

    it('preserves existing filters when adding new ones', async () => {
      const user = userEvent.setup();
      const existingFilters = { chapter: 'chapter-1' };
      
      render(<CardFilters {...defaultProps} filters={existingFilters} />);

      const difficultySelect = screen.getByLabelText('Difficulty');
      await user.selectOptions(difficultySelect, 'medium');

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        chapter: 'chapter-1',
        difficulty: 'medium',
      });
    });
  });

  describe('Clear Functionality', () => {
    it('clears all filters when Clear All button is clicked', async () => {
      const user = userEvent.setup();
      const filtersWithValues = {
        chapter: 'chapter-1',
        difficulty: 'easy',
        cardType: 'qa',
      };

      render(<CardFilters {...defaultProps} filters={filtersWithValues} />);

      const clearButton = screen.getByRole('button', { name: 'Clear All' });
      await user.click(clearButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({});
    });

    it('clears individual filters when filter tag X is clicked', async () => {
      const user = userEvent.setup();
      const filtersWithValues = {
        chapter: 'chapter-1',
        difficulty: 'easy',
        cardType: 'qa',
      };

      render(<CardFilters {...defaultProps} filters={filtersWithValues} />);

      // Find and click the X button for chapter filter
      const chapterTag = screen.getByText('Chapter: Introduction to Machine Learning').closest('span');
      const chapterRemoveButton = chapterTag?.querySelector('button');
      
      if (chapterRemoveButton) {
        await user.click(chapterRemoveButton);
      }

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        difficulty: 'easy',
        cardType: 'qa',
      });
    });
  });

  describe('Active Filters Display', () => {
    it('shows active filters section when filters are applied', () => {
      const filtersWithValues = {
        chapter: 'chapter-1',
        difficulty: 'easy',
        cardType: 'qa',
      };

      render(<CardFilters {...defaultProps} filters={filtersWithValues} />);

      expect(screen.getByText('Active filters:')).toBeInTheDocument();
      expect(screen.getByText('Chapter: Introduction to Machine Learning')).toBeInTheDocument();
      expect(screen.getByText('Easy (≤1.5)')).toBeInTheDocument();
      expect(screen.getByText('Q&A Cards')).toBeInTheDocument();
    });

    it('does not show active filters section when no filters are applied', () => {
      render(<CardFilters {...defaultProps} filters={{}} />);

      expect(screen.queryByText('Active filters:')).not.toBeInTheDocument();
    });

    it('shows correct chapter title in active filter tag', () => {
      const filtersWithChapter = { chapter: 'chapter-2' };

      render(<CardFilters {...defaultProps} filters={filtersWithChapter} />);

      expect(screen.getByText('Chapter: Neural Networks')).toBeInTheDocument();
    });

    it('shows chapter ID when chapter not found in list', () => {
      const filtersWithUnknownChapter = { chapter: 'unknown-chapter' };

      render(<CardFilters {...defaultProps} filters={filtersWithUnknownChapter} />);

      expect(screen.getByText('Chapter: unknown-chapter')).toBeInTheDocument();
    });

    it('applies correct styling to different filter tags', () => {
      const filtersWithValues = {
        chapter: 'chapter-1',
        difficulty: 'easy',
        cardType: 'qa',
      };

      render(<CardFilters {...defaultProps} filters={filtersWithValues} />);

      const chapterTag = screen.getByText('Chapter: Introduction to Machine Learning').closest('span');
      const difficultyTag = screen.getByText('Easy (≤1.5)').closest('span');
      const cardTypeTag = screen.getByText('Q&A Cards').closest('span');

      expect(chapterTag).toHaveClass('bg-blue-100', 'text-blue-800');
      expect(difficultyTag).toHaveClass('bg-green-100', 'text-green-800');
      expect(cardTypeTag).toHaveClass('bg-purple-100', 'text-purple-800');
    });
  });

  describe('Current Values Display', () => {
    it('displays current filter values in select elements', () => {
      const filtersWithValues = {
        chapter: 'chapter-1',
        difficulty: 'easy',
        cardType: 'qa',
      };

      render(<CardFilters {...defaultProps} filters={filtersWithValues} />);

      expect(screen.getByDisplayValue('Introduction to Machine Learning')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Easy (≤1.5)')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Q&A Cards')).toBeInTheDocument();
    });

    it('shows default values when no filters are applied', () => {
      render(<CardFilters {...defaultProps} filters={{}} />);

      expect(screen.getByDisplayValue('All Chapters')).toBeInTheDocument();
      expect(screen.getByDisplayValue('All Difficulties')).toBeInTheDocument();
      expect(screen.getByDisplayValue('All Types')).toBeInTheDocument();
    });
  });

  describe('Empty State Handling', () => {
    it('handles empty chapters array gracefully', () => {
      render(<CardFilters {...defaultProps} chapters={[]} />);

      const chapterSelect = screen.getByLabelText('Chapter');
      expect(chapterSelect).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'All Chapters' })).toBeInTheDocument();
    });

    it('handles undefined chapters gracefully', () => {
      render(<CardFilters {...defaultProps} chapters={undefined} />);

      const chapterSelect = screen.getByLabelText('Chapter');
      expect(chapterSelect).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'All Chapters' })).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <CardFilters {...defaultProps} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('maintains default styling with custom className', () => {
      const { container } = render(
        <CardFilters {...defaultProps} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('bg-white', 'rounded-lg', 'shadow-sm', 'custom-class');
    });
  });

  describe('Responsive Design', () => {
    it('applies responsive classes to filter containers', () => {
      render(<CardFilters {...defaultProps} />);

      const chapterContainer = screen.getByLabelText('Chapter').closest('div');
      const difficultyContainer = screen.getByLabelText('Difficulty').closest('div');
      const cardTypeContainer = screen.getByLabelText('Card Type').closest('div');

      expect(chapterContainer).toHaveClass('flex-1', 'min-w-48');
      expect(difficultyContainer).toHaveClass('flex-1', 'min-w-48');
      expect(cardTypeContainer).toHaveClass('flex-1', 'min-w-48');
    });

    it('applies flex-wrap to main container', () => {
      render(<CardFilters {...defaultProps} />);

      const mainContainer = screen.getByLabelText('Chapter').closest('.flex');
      expect(mainContainer).toHaveClass('flex-wrap', 'gap-4');
    });
  });

  describe('Accessibility', () => {
    it('has proper labels for all select elements', () => {
      render(<CardFilters {...defaultProps} />);

      expect(screen.getByLabelText('Chapter')).toBeInTheDocument();
      expect(screen.getByLabelText('Difficulty')).toBeInTheDocument();
      expect(screen.getByLabelText('Card Type')).toBeInTheDocument();
    });

    it('has proper IDs linking labels to inputs', () => {
      render(<CardFilters {...defaultProps} />);

      const chapterSelect = screen.getByLabelText('Chapter');
      const difficultySelect = screen.getByLabelText('Difficulty');
      const cardTypeSelect = screen.getByLabelText('Card Type');

      expect(chapterSelect).toHaveAttribute('id', 'chapter-filter');
      expect(difficultySelect).toHaveAttribute('id', 'difficulty-filter');
      expect(cardTypeSelect).toHaveAttribute('id', 'type-filter');
    });

    it('clear all button is accessible', () => {
      render(<CardFilters {...defaultProps} />);

      const clearButton = screen.getByRole('button', { name: 'Clear All' });
      expect(clearButton).toBeInTheDocument();
      expect(clearButton).not.toBeDisabled();
    });

    it('filter tag remove buttons are accessible', () => {
      const filtersWithValues = {
        chapter: 'chapter-1',
        difficulty: 'easy',
        cardType: 'qa',
      };

      render(<CardFilters {...defaultProps} filters={filtersWithValues} />);

      const removeButtons = screen.getAllByText('×');
      expect(removeButtons).toHaveLength(3);
      
      removeButtons.forEach(button => {
        expect(button.closest('button')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles selecting and deselecting same filter', async () => {
      const user = userEvent.setup();
      render(<CardFilters {...defaultProps} />);

      const chapterSelect = screen.getByLabelText('Chapter');
      
      // Select a chapter
      await user.selectOptions(chapterSelect, 'chapter-1');
      expect(mockOnFiltersChange).toHaveBeenCalledWith({ chapter: 'chapter-1' });

      // Deselect (select "All Chapters")
      await user.selectOptions(chapterSelect, '');
      expect(mockOnFiltersChange).toHaveBeenCalledWith({});
    });

    it('handles rapid filter changes', async () => {
      const user = userEvent.setup();
      render(<CardFilters {...defaultProps} />);

      const chapterSelect = screen.getByLabelText('Chapter');
      
      // Rapid selections
      await user.selectOptions(chapterSelect, 'chapter-1');
      await user.selectOptions(chapterSelect, 'chapter-2');
      await user.selectOptions(chapterSelect, 'chapter-3');

      expect(mockOnFiltersChange).toHaveBeenCalledTimes(3);
      expect(mockOnFiltersChange).toHaveBeenLastCalledWith({ chapter: 'chapter-3' });
    });

    it('handles filter removal when multiple filters are active', async () => {
      const user = userEvent.setup();
      const filtersWithMultipleValues = {
        chapter: 'chapter-1',
        difficulty: 'easy',
        cardType: 'qa',
      };

      render(<CardFilters {...defaultProps} filters={filtersWithMultipleValues} />);

      // Remove difficulty filter
      const difficultyTag = screen.getByText('Easy (≤1.5)').closest('span');
      const difficultyRemoveButton = difficultyTag?.querySelector('button');
      
      if (difficultyRemoveButton) {
        await user.click(difficultyRemoveButton);
      }

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        chapter: 'chapter-1',
        cardType: 'qa',
      });
    });
  });
});