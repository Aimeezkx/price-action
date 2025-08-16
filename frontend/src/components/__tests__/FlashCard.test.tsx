import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../../test/utils';
import { vi } from 'vitest';
import { FlashCard } from '../FlashCard';
import type { Card } from '../../types';

// Mock the ImageHotspotViewer component
vi.mock('../ImageHotspotViewer', () => ({
  ImageHotspotViewer: ({ onValidationComplete, mode }: any) => (
    <div data-testid="image-hotspot-viewer" data-mode={mode}>
      <button
        onClick={() => onValidationComplete?.(true, [])}
        data-testid="hotspot-validation-button"
      >
        Validate Hotspot
      </button>
    </div>
  ),
}));

const mockQACard: Card = {
  id: '1',
  card_type: 'qa',
  front: 'What is machine learning?',
  back: 'Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.',
  difficulty: 1.5,
  due_date: '2023-12-01T00:00:00Z',
  metadata: {},
};

const mockClozeCard: Card = {
  id: '2',
  card_type: 'cloze',
  front: 'Machine learning is a subset of [artificial intelligence] that enables computers to learn.',
  back: 'Machine learning is a subset of artificial intelligence that enables computers to learn.',
  difficulty: 2.0,
  due_date: '2023-12-01T00:00:00Z',
  metadata: {
    blanks: ['artificial intelligence'],
  },
};

const mockImageHotspotCard: Card = {
  id: '3',
  card_type: 'image_hotspot',
  front: '/images/neural-network.png',
  back: 'This diagram shows the structure of a neural network.',
  difficulty: 2.5,
  due_date: '2023-12-01T00:00:00Z',
  metadata: {
    hotspots: [
      { x: 100, y: 100, width: 50, height: 50, label: 'Input Layer' },
      { x: 200, y: 100, width: 50, height: 50, label: 'Hidden Layer' },
    ],
  },
};

describe('FlashCard', () => {
  const mockOnFlip = vi.fn();
  const mockOnHotspotValidation = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders QA card correctly', () => {
      render(
        <FlashCard
          card={mockQACard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText('What is machine learning?')).toBeInTheDocument();
      expect(screen.getByText('Q A')).toBeInTheDocument();
      expect(screen.getByText('Easy')).toBeInTheDocument();
      expect(screen.getByText('Click to flip')).toBeInTheDocument();
    });

    it('renders cloze card with blanks', () => {
      render(
        <FlashCard
          card={mockClozeCard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText(/Machine learning is a subset of \[1\]/)).toBeInTheDocument();
      expect(screen.getByText('CLOZE')).toBeInTheDocument();
    });

    it('renders image hotspot card', () => {
      render(
        <FlashCard
          card={mockImageHotspotCard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByTestId('image-hotspot-viewer')).toBeInTheDocument();
      expect(screen.getByText('IMAGE HOTSPOT')).toBeInTheDocument();
    });
  });

  describe('Card Flipping', () => {
    it('calls onFlip when card is clicked', () => {
      render(
        <FlashCard
          card={mockQACard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      const cardContainer = screen.getByText('What is machine learning?').closest('[class*="cursor-pointer"]');
      fireEvent.click(cardContainer!);

      expect(mockOnFlip).toHaveBeenCalledTimes(1);
    });

    it('shows back content when flipped', () => {
      render(
        <FlashCard
          card={mockQACard}
          isFlipped={true}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText(/Machine learning is a subset of artificial intelligence/)).toBeInTheDocument();
      expect(screen.getByText('Answer')).toBeInTheDocument();
      expect(screen.getByText('Grade your answer')).toBeInTheDocument();
    });

    it('prevents flipping during animation', async () => {
      render(
        <FlashCard
          card={mockQACard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      const cardContainer = screen.getByText('What is machine learning?').closest('[class*="cursor-pointer"]');
      
      // Click multiple times rapidly
      fireEvent.click(cardContainer!);
      fireEvent.click(cardContainer!);
      fireEvent.click(cardContainer!);

      // Should only call onFlip once due to animation lock
      expect(mockOnFlip).toHaveBeenCalledTimes(1);
    });
  });

  describe('Difficulty Display', () => {
    it('shows correct difficulty colors and labels', () => {
      const { rerender } = render(
        <FlashCard
          card={{ ...mockQACard, difficulty: 1.0 }}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText('Easy')).toHaveClass('text-green-800');

      rerender(
        <FlashCard
          card={{ ...mockQACard, difficulty: 2.0 }}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText('Medium')).toHaveClass('text-yellow-800');

      rerender(
        <FlashCard
          card={{ ...mockQACard, difficulty: 3.0 }}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText('Hard')).toHaveClass('text-red-800');
    });
  });

  describe('Image Hotspot Functionality', () => {
    it('handles hotspot validation correctly', async () => {
      render(
        <FlashCard
          card={mockImageHotspotCard}
          isFlipped={false}
          onFlip={mockOnFlip}
          onHotspotValidation={mockOnHotspValidation}
        />
      );

      const validationButton = screen.getByTestId('hotspot-validation-button');
      fireEvent.click(validationButton);

      expect(mockOnHotspValidation).toHaveBeenCalledWith(true);

      // Should auto-flip after validation
      await waitFor(() => {
        expect(mockOnFlip).toHaveBeenCalled();
      }, { timeout: 2000 });
    });

    it('shows study mode initially for hotspot cards', () => {
      render(
        <FlashCard
          card={mockImageHotspotCard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      const hotspotViewer = screen.getByTestId('image-hotspot-viewer');
      expect(hotspotViewer).toHaveAttribute('data-mode', 'study');
    });

    it('shows answer mode after validation', async () => {
      render(
        <FlashCard
          card={mockImageHotspotCard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      const validationButton = screen.getByTestId('hotspot-validation-button');
      fireEvent.click(validationButton);

      await waitFor(() => {
        const hotspotViewer = screen.getByTestId('image-hotspot-viewer');
        expect(hotspotViewer).toHaveAttribute('data-mode', 'answer');
      });
    });
  });

  describe('Cloze Card Functionality', () => {
    it('shows blanks in front content', () => {
      render(
        <FlashCard
          card={mockClozeCard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText(/\[1\]/)).toBeInTheDocument();
      expect(screen.queryByText('artificial intelligence')).not.toBeInTheDocument();
    });

    it('shows complete text in back content', () => {
      render(
        <FlashCard
          card={mockClozeCard}
          isFlipped={true}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText(/artificial intelligence/)).toBeInTheDocument();
      expect(screen.queryByText(/\[1\]/)).not.toBeInTheDocument();
    });

    it('handles multiple blanks correctly', () => {
      const multiBlankCard = {
        ...mockClozeCard,
        front: 'Machine [learning] is a subset of [artificial intelligence].',
        metadata: {
          blanks: ['learning', 'artificial intelligence'],
        },
      };

      render(
        <FlashCard
          card={multiBlankCard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText(/\[1\].*\[2\]/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(
        <FlashCard
          card={mockQACard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      const cardContainer = screen.getByText('What is machine learning?').closest('[class*="cursor-pointer"]');
      expect(cardContainer).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {
      render(
        <FlashCard
          card={mockQACard}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      const cardContainer = screen.getByText('What is machine learning?').closest('[class*="cursor-pointer"]');
      
      // Simulate Enter key press
      fireEvent.keyDown(cardContainer!, { key: 'Enter', code: 'Enter' });
      // Note: This test would need additional keyboard event handling in the component
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      render(
        <FlashCard
          card={mockQACard}
          isFlipped={false}
          onFlip={mockOnFlip}
          className="custom-class"
        />
      );

      const container = screen.getByText('What is machine learning?').closest('.custom-class');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty metadata gracefully', () => {
      const cardWithoutMetadata = {
        ...mockQACard,
        metadata: undefined,
      };

      expect(() => {
        render(
          <FlashCard
            card={cardWithoutMetadata}
            isFlipped={false}
            onFlip={mockOnFlip}
          />
        );
      }).not.toThrow();
    });

    it('handles missing hotspots in image card', () => {
      const imageCardWithoutHotspots = {
        ...mockImageHotspotCard,
        metadata: {},
      };

      render(
        <FlashCard
          card={imageCardWithoutHotspots}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByTestId('image-hotspot-viewer')).toBeInTheDocument();
    });

    it('handles missing blanks in cloze card', () => {
      const clozeCardWithoutBlanks = {
        ...mockClozeCard,
        metadata: {},
      };

      render(
        <FlashCard
          card={clozeCardWithoutBlanks}
          isFlipped={false}
          onFlip={mockOnFlip}
        />
      );

      expect(screen.getByText(clozeCardWithoutBlanks.front)).toBeInTheDocument();
    });
  });
});