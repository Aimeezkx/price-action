import React from 'react';
import { render, screen, fireEvent } from '../../../test/utils';
import { vi } from 'vitest';
import { SearchResults } from '../SearchResults';
import type { SearchResult } from '../../types';

// Mock Heroicons
vi.mock('@heroicons/react/24/outline', () => ({
  DocumentTextIcon: ({ className }: { className?: string }) => (
    <svg className={className} data-testid="document-text-icon" />
  ),
  AcademicCapIcon: ({ className }: { className?: string }) => (
    <svg className={className} data-testid="academic-cap-icon" />
  ),
  ChartBarIcon: ({ className }: { className?: string }) => (
    <svg className={className} data-testid="chart-bar-icon" />
  ),
  ClockIcon: ({ className }: { className?: string }) => (
    <svg className={className} data-testid="clock-icon" />
  ),
  TagIcon: ({ className }: { className?: string }) => (
    <svg className={className} data-testid="tag-icon" />
  ),
  BookOpenIcon: ({ className }: { className?: string }) => (
    <svg className={className} data-testid="book-open-icon" />
  ),
}));

const mockSearchResults: SearchResult[] = [
  {
    id: '1',
    title: 'Machine Learning Basics',
    content: 'Machine learning is a subset of artificial intelligence that enables computers to learn from data.',
    type: 'knowledge',
    score: 0.95,
    highlights: ['machine learning', 'artificial intelligence'],
    chapter_title: 'Introduction',
    metadata: {
      kind: 'definition',
      entities: ['machine learning', 'AI', 'data'],
      anchors: { page: 1, chapter: 1, position: 100 },
      difficulty: 1.2,
      rank_factors: {
        text_match: 0.9,
        semantic_similarity: 0.8,
        entity_match: 0.7,
      },
    },
  },
  {
    id: '2',
    title: 'Neural Network Architecture',
    content: 'Neural networks consist of interconnected nodes that process information.',
    type: 'card',
    score: 0.87,
    highlights: ['neural networks'],
    chapter_title: 'Deep Learning',
    metadata: {
      kind: 'concept',
      entities: ['neural networks', 'nodes'],
      anchors: { page: 15, chapter: 3, position: 500 },
      difficulty: 2.8,
    },
  },
];

describe('SearchResults', () => {
  const mockOnResultClick = vi.fn();

  const defaultProps = {
    results: mockSearchResults,
    totalResults: 2,
    query: 'machine learning',
    onResultClick: mockOnResultClick,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders search results correctly', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('Machine Learning Basics')).toBeInTheDocument();
      expect(screen.getByText('Neural Network Architecture')).toBeInTheDocument();
    });

    it('displays total results count', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('2 results found')).toBeInTheDocument();
    });

    it('displays search completion indicator', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('Search completed')).toBeInTheDocument();
      expect(screen.getByTestId('clock-icon')).toBeInTheDocument();
    });

    it('handles singular result count', () => {
      render(<SearchResults {...defaultProps} totalResults={1} />);

      expect(screen.getByText('1 result found')).toBeInTheDocument();
    });
  });

  describe('Result Content', () => {
    it('displays result titles and content', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('Machine Learning Basics')).toBeInTheDocument();
      expect(screen.getByText(/Machine learning is a subset of artificial intelligence/)).toBeInTheDocument();
      expect(screen.getByText('Neural Network Architecture')).toBeInTheDocument();
      expect(screen.getByText(/Neural networks consist of interconnected nodes/)).toBeInTheDocument();
    });

    it('displays result type badges', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('Knowledge Point')).toBeInTheDocument();
      expect(screen.getByText('Flashcard')).toBeInTheDocument();
    });

    it('displays chapter information', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('Introduction')).toBeInTheDocument();
      expect(screen.getByText('Deep Learning')).toBeInTheDocument();
    });

    it('displays page numbers', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('Page 1')).toBeInTheDocument();
      expect(screen.getByText('Page 15')).toBeInTheDocument();
    });

    it('displays entity tags', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('machine learning, AI, data')).toBeInTheDocument();
      expect(screen.getByText('neural networks, nodes')).toBeInTheDocument();
    });
  });

  describe('Result Icons', () => {
    it('displays correct icons for different result types', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByTestId('document-text-icon')).toBeInTheDocument(); // Knowledge point
      expect(screen.getByTestId('academic-cap-icon')).toBeInTheDocument(); // Flashcard
    });

    it('displays default icon for unknown types', () => {
      const resultsWithUnknownType = [
        { ...mockSearchResults[0], type: 'unknown' },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithUnknownType} />);

      expect(screen.getByTestId('book-open-icon')).toBeInTheDocument();
    });
  });

  describe('Difficulty Display', () => {
    it('displays difficulty badges with correct colors', () => {
      render(<SearchResults {...defaultProps} />);

      // Easy difficulty (1.2)
      const easyBadge = screen.getByText('Easy');
      expect(easyBadge).toHaveClass('text-green-600');

      // Hard difficulty (2.8)
      const hardBadge = screen.getByText('Hard');
      expect(hardBadge).toHaveClass('text-red-600');
    });

    it('handles medium difficulty correctly', () => {
      const resultsWithMediumDifficulty = [
        { ...mockSearchResults[0], metadata: { ...mockSearchResults[0].metadata, difficulty: 2.0 } },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithMediumDifficulty} />);

      const mediumBadge = screen.getByText('Medium');
      expect(mediumBadge).toHaveClass('text-yellow-600');
    });

    it('handles missing difficulty gracefully', () => {
      const resultsWithoutDifficulty = [
        { ...mockSearchResults[0], metadata: { ...mockSearchResults[0].metadata, difficulty: undefined } },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithoutDifficulty} />);

      expect(screen.queryByText('Easy')).not.toBeInTheDocument();
      expect(screen.queryByText('Medium')).not.toBeInTheDocument();
      expect(screen.queryByText('Hard')).not.toBeInTheDocument();
    });
  });

  describe('Score Display', () => {
    it('displays search scores as percentages', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('Score: 95%')).toBeInTheDocument();
      expect(screen.getByText('Score: 87%')).toBeInTheDocument();
    });

    it('handles missing scores gracefully', () => {
      const resultsWithoutScore = [
        { ...mockSearchResults[0], score: undefined },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithoutScore} />);

      expect(screen.queryByText(/Score:/)).not.toBeInTheDocument();
    });
  });

  describe('Text Highlighting', () => {
    it('highlights search terms in content', () => {
      render(<SearchResults {...defaultProps} />);

      // Check for highlighted terms (mark elements)
      const highlightedElements = screen.getAllByText('machine learning');
      expect(highlightedElements.length).toBeGreaterThan(0);
    });

    it('falls back to query-based highlighting when no highlights provided', () => {
      const resultsWithoutHighlights = [
        { ...mockSearchResults[0], highlights: undefined },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithoutHighlights} />);

      // Should still highlight based on query
      expect(screen.getByText('Machine Learning Basics')).toBeInTheDocument();
    });

    it('handles empty highlights array', () => {
      const resultsWithEmptyHighlights = [
        { ...mockSearchResults[0], highlights: [] },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithEmptyHighlights} />);

      expect(screen.getByText('Machine Learning Basics')).toBeInTheDocument();
    });
  });

  describe('Ranking Factors', () => {
    it('displays ranking factors in expandable details', () => {
      render(<SearchResults {...defaultProps} />);

      const rankingFactorsToggle = screen.getByText('Ranking factors');
      expect(rankingFactorsToggle).toBeInTheDocument();

      // Expand details
      fireEvent.click(rankingFactorsToggle);

      expect(screen.getByText('Text match')).toBeInTheDocument();
      expect(screen.getByText('90.0%')).toBeInTheDocument();
      expect(screen.getByText('Semantic similarity')).toBeInTheDocument();
      expect(screen.getByText('80.0%')).toBeInTheDocument();
    });

    it('handles missing ranking factors gracefully', () => {
      const resultsWithoutRankingFactors = [
        { ...mockSearchResults[0], metadata: { ...mockSearchResults[0].metadata, rank_factors: undefined } },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithoutRankingFactors} />);

      expect(screen.queryByText('Ranking factors')).not.toBeInTheDocument();
    });
  });

  describe('Entity Handling', () => {
    it('displays first 3 entities and shows count for more', () => {
      const resultsWithManyEntities = [
        {
          ...mockSearchResults[0],
          metadata: {
            ...mockSearchResults[0].metadata,
            entities: ['entity1', 'entity2', 'entity3', 'entity4', 'entity5'],
          },
        },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithManyEntities} />);

      expect(screen.getByText('entity1, entity2, entity3 +2 more')).toBeInTheDocument();
    });

    it('displays all entities when 3 or fewer', () => {
      render(<SearchResults {...defaultProps} />);

      expect(screen.getByText('machine learning, AI, data')).toBeInTheDocument();
      expect(screen.queryByText('+0 more')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('displays loading skeletons when loading', () => {
      render(<SearchResults {...defaultProps} isLoading={true} />);

      const skeletons = screen.getAllByRole('generic');
      const animatedElements = skeletons.filter(el => el.classList.contains('animate-pulse'));
      expect(animatedElements.length).toBeGreaterThan(0);
    });

    it('does not display results when loading', () => {
      render(<SearchResults {...defaultProps} isLoading={true} />);

      expect(screen.queryByText('Machine Learning Basics')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('displays no results message when no results and query exists', () => {
      render(<SearchResults {...defaultProps} results={[]} totalResults={0} />);

      expect(screen.getByText('No results found')).toBeInTheDocument();
      expect(screen.getByText(/Try adjusting your search terms/)).toBeInTheDocument();
    });

    it('displays document icon in empty state', () => {
      render(<SearchResults {...defaultProps} results={[]} totalResults={0} />);

      expect(screen.getByTestId('document-text-icon')).toBeInTheDocument();
    });

    it('does not display empty state when no query', () => {
      render(<SearchResults {...defaultProps} results={[]} totalResults={0} query="" />);

      expect(screen.queryByText('No results found')).not.toBeInTheDocument();
    });
  });

  describe('Click Handling', () => {
    it('calls onResultClick when result is clicked', () => {
      render(<SearchResults {...defaultProps} />);

      const firstResult = screen.getByText('Machine Learning Basics').closest('div[class*="cursor-pointer"]');
      fireEvent.click(firstResult!);

      expect(mockOnResultClick).toHaveBeenCalledWith(mockSearchResults[0]);
    });

    it('handles missing onResultClick gracefully', () => {
      render(<SearchResults {...defaultProps} onResultClick={undefined} />);

      const firstResult = screen.getByText('Machine Learning Basics').closest('div[class*="cursor-pointer"]');
      
      expect(() => {
        fireEvent.click(firstResult!);
      }).not.toThrow();
    });
  });

  describe('Hover Effects', () => {
    it('applies hover classes to result cards', () => {
      render(<SearchResults {...defaultProps} />);

      const resultCards = screen.getAllByRole('generic').filter(el => 
        el.classList.contains('hover:border-gray-300')
      );
      expect(resultCards.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      render(<SearchResults {...defaultProps} />);

      // Results should be in a list-like structure
      const resultCards = screen.getAllByText(/Machine Learning|Neural Network/).map(el => 
        el.closest('div[class*="cursor-pointer"]')
      );
      expect(resultCards.length).toBe(2);
    });

    it('result cards are clickable', () => {
      render(<SearchResults {...defaultProps} />);

      const resultCards = screen.getAllByRole('generic').filter(el => 
        el.classList.contains('cursor-pointer')
      );
      expect(resultCards.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('handles results without metadata', () => {
      const resultsWithoutMetadata = [
        { ...mockSearchResults[0], metadata: undefined },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithoutMetadata} />);

      expect(screen.getByText('Machine Learning Basics')).toBeInTheDocument();
    });

    it('handles results without chapter title', () => {
      const resultsWithoutChapter = [
        { ...mockSearchResults[0], chapter_title: undefined },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithoutChapter} />);

      expect(screen.getByText('Machine Learning Basics')).toBeInTheDocument();
    });

    it('handles very long content gracefully', () => {
      const resultsWithLongContent = [
        {
          ...mockSearchResults[0],
          content: 'This is a very long content that should be truncated or handled gracefully by the component to ensure proper display and user experience. '.repeat(10),
        },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithLongContent} />);

      expect(screen.getByText('Machine Learning Basics')).toBeInTheDocument();
    });

    it('handles special characters in content', () => {
      const resultsWithSpecialChars = [
        {
          ...mockSearchResults[0],
          content: 'Content with special chars: <>&"\'',
          title: 'Title with special chars: <>&"\'',
        },
      ];

      render(<SearchResults {...defaultProps} results={resultsWithSpecialChars} />);

      expect(screen.getByText('Title with special chars: <>&"\'')).toBeInTheDocument();
    });
  });
});