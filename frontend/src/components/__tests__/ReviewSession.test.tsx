import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../../test/utils';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { ReviewSession } from '../ReviewSession';
import { testAccessibility, testKeyboardNavigation } from '../../test/accessibility';
import { testResponsiveDesign } from '../../test/visual-regression';
import type { Card } from '../../types';

// Mock child components
vi.mock('../FlashCard', () => ({
  FlashCard: ({ card, isFlipped, onFlip, onHotspotValidation }: any) => (
    <div data-testid="flash-card" data-card-id={card.id} data-flipped={isFlipped}>
      <div onClick={onFlip}>{card.front}</div>
      {card.card_type === 'image_hotspot' && (
        <button onClick={() => onHotspotValidation?.(true)} data-testid="hotspot-validate">
          Validate
        </button>
      )}
    </div>
  ),
}));

vi.mock('../GradingInterface', () => ({
  GradingInterface: ({ onGrade, disabled }: any) => (
    <div data-testid="grading-interface" data-disabled={disabled}>
      {[1, 2, 3, 4, 5].map(grade => (
        <button
          key={grade}
          onClick={() => onGrade(grade)}
          data-testid={`grade-${grade}`}
          disabled={disabled}
        >
          Grade {grade}
        </button>
      ))}
    </div>
  ),
}));

vi.mock('../LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
}));

const mockCards: Card[] = [
  {
    id: '1',
    card_type: 'qa',
    front: 'What is machine learning?',
    back: 'Machine learning is a subset of artificial intelligence...',
    difficulty: 1.5,
    due_date: '2023-12-01T00:00:00Z',
    metadata: {},
  },
  {
    id: '2',
    card_type: 'cloze',
    front: 'Machine learning is a subset of [artificial intelligence].',
    back: 'Machine learning is a subset of artificial intelligence.',
    difficulty: 2.0,
    due_date: '2023-12-02T00:00:00Z',
    metadata: { blanks: ['artificial intelligence'] },
  },
  {
    id: '3',
    card_type: 'image_hotspot',
    front: '/images/neural-network.png',
    back: 'This diagram shows a neural network.',
    difficulty: 2.5,
    due_date: '2023-12-03T00:00:00Z',
    metadata: { hotspots: [{ x: 100, y: 100, width: 50, height: 50, label: 'Input Layer' }] },
  },
];

// Mock the useGradeCard hook
vi.mock('../../hooks/useCards', () => ({
  useGradeCard: vi.fn(),
}));

describe('ReviewSession', () => {
  const mockGradeCardMutation = {
    mutateAsync: vi.fn(),
    isPending: false,
    error: null,
    reset: vi.fn(),
  };

  const mockOnSessionComplete = vi.fn();
  const mockOnSessionExit = vi.fn();

  const defaultProps = {
    cards: mockCards,
    onSessionComplete: mockOnSessionComplete,
    onSessionExit: mockOnSessionExit,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    const { useGradeCard } = vi.mocked(await import('../../hooks/useCards'));
    useGradeCard.mockReturnValue(mockGradeCardMutation);
  });

  describe('Basic Rendering', () => {
    it('renders review session with first card', () => {
      render(<ReviewSession {...defaultProps} />);

      expect(screen.getByTestId('flash-card')).toBeInTheDocument();
      expect(screen.getByText('What is machine learning?')).toBeInTheDocument();
      expect(screen.getByText('Card 1 of 3')).toBeInTheDocument();
    });

    it('renders progress indicator', () => {
      render(<ReviewSession {...defaultProps} />);

      expect(screen.getByText('Card 1 of 3')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('renders grading interface when card is flipped', async () => {
      render(<ReviewSession {...defaultProps} />);

      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });
    });

    it('shows session stats', () => {
      render(<ReviewSession {...defaultProps} />);

      expect(screen.getByText('0 reviewed')).toBeInTheDocument();
      expect(screen.getByText('3 remaining')).toBeInTheDocument();
    });
  });

  describe('Card Navigation', () => {
    it('advances to next card after grading', async () => {
      render(<ReviewSession {...defaultProps} />);

      // Flip first card
      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      // Grade the card
      const gradeButton = screen.getByTestId('grade-4');
      fireEvent.click(gradeButton);

      await waitFor(() => {
        expect(screen.getByText('Card 2 of 3')).toBeInTheDocument();
        expect(screen.getByText('Machine learning is a subset of [artificial intelligence].')).toBeInTheDocument();
      });

      expect(mockOnGradeCard).toHaveBeenCalledWith('1', 4);
    });

    it('completes session after grading all cards', async () => {
      render(<ReviewSession {...defaultProps} />);

      // Grade all three cards
      for (let i = 0; i < 3; i++) {
        const card = screen.getByTestId('flash-card');
        fireEvent.click(card);

        await waitFor(() => {
          expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
        });

        const gradeButton = screen.getByTestId('grade-4');
        fireEvent.click(gradeButton);

        if (i < 2) {
          await waitFor(() => {
            expect(screen.getByText(`Card ${i + 2} of 3`)).toBeInTheDocument();
          });
        }
      }

      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalled();
      });
    });

    it('updates progress correctly', async () => {
      render(<ReviewSession {...defaultProps} />);

      // Grade first card
      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      const gradeButton = screen.getByTestId('grade-4');
      fireEvent.click(gradeButton);

      await waitFor(() => {
        expect(screen.getByText('1 reviewed')).toBeInTheDocument();
        expect(screen.getByText('2 remaining')).toBeInTheDocument();
      });

      // Check progress bar
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '33'); // 1/3 = 33%
    });
  });

  describe('Card Types', () => {
    it('handles QA cards correctly', () => {
      render(<ReviewSession {...defaultProps} />);

      expect(screen.getByText('What is machine learning?')).toBeInTheDocument();
      expect(screen.getByTestId('flash-card')).toHaveAttribute('data-card-id', '1');
    });

    it('handles cloze cards correctly', async () => {
      render(<ReviewSession {...defaultProps} />);

      // Skip to second card (cloze)
      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      const gradeButton = screen.getByTestId('grade-4');
      fireEvent.click(gradeButton);

      await waitFor(() => {
        expect(screen.getByText('Machine learning is a subset of [artificial intelligence].')).toBeInTheDocument();
      });
    });

    it('handles image hotspot cards correctly', async () => {
      render(<ReviewSession {...defaultProps} />);

      // Skip to third card (image hotspot)
      for (let i = 0; i < 2; i++) {
        const card = screen.getByTestId('flash-card');
        fireEvent.click(card);

        await waitFor(() => {
          expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
        });

        const gradeButton = screen.getByTestId('grade-4');
        fireEvent.click(gradeButton);
      }

      await waitFor(() => {
        expect(screen.getByTestId('hotspot-validate')).toBeInTheDocument();
      });

      // Validate hotspot
      const validateButton = screen.getByTestId('hotspot-validate');
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      render(<ReviewSession {...defaultProps} isLoading={true} />);

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(screen.queryByTestId('flash-card')).not.toBeInTheDocument();
    });

    it('disables grading when processing', async () => {
      render(<ReviewSession {...defaultProps} isGrading={true} />);

      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        const gradingInterface = screen.getByTestId('grading-interface');
        expect(gradingInterface).toHaveAttribute('data-disabled', 'true');
      });
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no cards', () => {
      render(<ReviewSession {...defaultProps} cards={[]} />);

      expect(screen.getByText('No cards to review')).toBeInTheDocument();
      expect(screen.getByText('All caught up! Check back later for more cards to review.')).toBeInTheDocument();
    });

    it('calls onComplete immediately when no cards', () => {
      render(<ReviewSession {...defaultProps} cards={[]} />);

      expect(mockOnComplete).toHaveBeenCalled();
    });
  });

  describe('Keyboard Navigation', () => {
    it('supports keyboard navigation for card flipping', async () => {
      const user = userEvent.setup();
      render(<ReviewSession {...defaultProps} />);

      const card = screen.getByTestId('flash-card');
      
      // Focus and press Enter to flip
      card.focus();
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation for grading', async () => {
      const user = userEvent.setup();
      render(<ReviewSession {...defaultProps} />);

      // Flip card first
      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      // Use keyboard to grade
      const gradeButton = screen.getByTestId('grade-4');
      gradeButton.focus();
      await user.keyboard('{Enter}');

      expect(mockOnGradeCard).toHaveBeenCalledWith('1', 4);
    });

    it('supports number key shortcuts for grading', async () => {
      const user = userEvent.setup();
      render(<ReviewSession {...defaultProps} />);

      // Flip card
      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      // Use number key shortcut
      await user.keyboard('4');

      expect(mockOnGradeCard).toHaveBeenCalledWith('1', 4);
    });
  });

  describe('Session Statistics', () => {
    it('tracks correct and incorrect answers', async () => {
      render(<ReviewSession {...defaultProps} />);

      // Grade first card as correct (4 or 5)
      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      const gradeButton = screen.getByTestId('grade-5');
      fireEvent.click(gradeButton);

      await waitFor(() => {
        expect(screen.getByText('1 correct')).toBeInTheDocument();
        expect(screen.getByText('0 incorrect')).toBeInTheDocument();
      });
    });

    it('calculates accuracy percentage', async () => {
      render(<ReviewSession {...defaultProps} />);

      // Grade first card as correct
      let card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      let gradeButton = screen.getByTestId('grade-5');
      fireEvent.click(gradeButton);

      // Grade second card as incorrect
      await waitFor(() => {
        card = screen.getByTestId('flash-card');
      });

      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      gradeButton = screen.getByTestId('grade-2');
      fireEvent.click(gradeButton);

      await waitFor(() => {
        expect(screen.getByText('50% accuracy')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles grading errors gracefully', async () => {
      const mockOnGradeCardWithError = vi.fn().mockRejectedValue(new Error('Grading failed'));
      
      render(<ReviewSession {...defaultProps} onGradeCard={mockOnGradeCardWithError} />);

      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      const gradeButton = screen.getByTestId('grade-4');
      fireEvent.click(gradeButton);

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/Failed to grade card/)).toBeInTheDocument();
      });
    });

    it('allows retry after grading error', async () => {
      const mockOnGradeCardWithError = vi.fn()
        .mockRejectedValueOnce(new Error('Grading failed'))
        .mockResolvedValueOnce(undefined);
      
      render(<ReviewSession {...defaultProps} onGradeCard={mockOnGradeCardWithError} />);

      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      const gradeButton = screen.getByTestId('grade-4');
      fireEvent.click(gradeButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to grade card/)).toBeInTheDocument();
      });

      // Retry
      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Card 2 of 3')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('meets accessibility standards', async () => {
      const { container } = render(<ReviewSession {...defaultProps} />);
      
      await testAccessibility(container);
    });

    it('has proper keyboard navigation', () => {
      const { container } = render(<ReviewSession {...defaultProps} />);
      
      const keyboardResults = testKeyboardNavigation(container);
      expect(keyboardResults.totalFocusableElements).toBeGreaterThan(0);
    });

    it('has proper ARIA labels', () => {
      render(<ReviewSession {...defaultProps} />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-label', 'Review progress');
      expect(progressBar).toHaveAttribute('aria-valuenow', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '3');
    });

    it('announces progress changes to screen readers', async () => {
      render(<ReviewSession {...defaultProps} />);

      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      const gradeButton = screen.getByTestId('grade-4');
      fireEvent.click(gradeButton);

      await waitFor(() => {
        const announcement = screen.getByRole('status', { hidden: true });
        expect(announcement).toHaveTextContent('Card 2 of 3');
      });
    });
  });

  describe('Responsive Design', () => {
    it('adapts to different screen sizes', async () => {
      const { container } = render(<ReviewSession {...defaultProps} />);
      
      const visualResults = await testResponsiveDesign(container, 'ReviewSession');
      expect(visualResults.every(result => result.passed)).toBe(true);
    });

    it('maintains usability on mobile devices', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<ReviewSession {...defaultProps} />);

      // Touch targets should be large enough
      const card = screen.getByTestId('flash-card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('renders efficiently with large card sets', () => {
      const manyCards = Array.from({ length: 100 }, (_, i) => ({
        ...mockCards[0],
        id: `card-${i}`,
        front: `Question ${i}`,
      }));

      const startTime = performance.now();
      render(<ReviewSession {...defaultProps} cards={manyCards} />);
      const endTime = performance.now();

      // Should render quickly even with many cards
      expect(endTime - startTime).toBeLessThan(100);
    });

    it('only renders current card to optimize performance', () => {
      render(<ReviewSession {...defaultProps} />);

      // Should only render one card at a time
      const cards = screen.getAllByTestId('flash-card');
      expect(cards).toHaveLength(1);
    });
  });

  describe('Session Persistence', () => {
    it('maintains session state during component updates', async () => {
      const { rerender } = render(<ReviewSession {...defaultProps} />);

      // Grade first card
      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      const gradeButton = screen.getByTestId('grade-4');
      fireEvent.click(gradeButton);

      await waitFor(() => {
        expect(screen.getByText('Card 2 of 3')).toBeInTheDocument();
      });

      // Rerender with same props
      rerender(<ReviewSession {...defaultProps} />);

      // Should maintain progress
      expect(screen.getByText('Card 2 of 3')).toBeInTheDocument();
      expect(screen.getByText('1 reviewed')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles single card session', async () => {
      render(<ReviewSession {...defaultProps} cards={[mockCards[0]]} />);

      expect(screen.getByText('Card 1 of 1')).toBeInTheDocument();

      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      const gradeButton = screen.getByTestId('grade-4');
      fireEvent.click(gradeButton);

      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalled();
      });
    });

    it('handles cards with missing metadata', () => {
      const cardsWithoutMetadata = [
        { ...mockCards[0], metadata: undefined },
      ];

      render(<ReviewSession {...defaultProps} cards={cardsWithoutMetadata} />);

      expect(screen.getByTestId('flash-card')).toBeInTheDocument();
    });

    it('handles rapid grading attempts', async () => {
      render(<ReviewSession {...defaultProps} />);

      const card = screen.getByTestId('flash-card');
      fireEvent.click(card);

      await waitFor(() => {
        expect(screen.getByTestId('grading-interface')).toBeInTheDocument();
      });

      const gradeButton = screen.getByTestId('grade-4');
      
      // Rapid clicks should only register once
      fireEvent.click(gradeButton);
      fireEvent.click(gradeButton);
      fireEvent.click(gradeButton);

      expect(mockOnGradeCard).toHaveBeenCalledTimes(1);
    });
  });
});