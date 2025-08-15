import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { FlashCard } from '../FlashCard';
import { Card } from '../../types';

const mockCard: Card = {
  id: '1',
  front: 'What is React Native?',
  back: 'A framework for building mobile apps using React',
  cardType: 'qa',
  difficulty: 2.5,
  dueDate: new Date(),
  metadata: {},
};

const mockImageCard: Card = {
  id: '2',
  front: 'image-path.jpg',
  back: 'Image description',
  cardType: 'image_hotspot',
  difficulty: 3.0,
  dueDate: new Date(),
  metadata: {
    hotspots: [
      { x: 100, y: 100, width: 50, height: 50, label: 'Feature A' },
    ],
  },
};

describe('FlashCard', () => {
  it('renders front side initially', () => {
    const { getByText } = render(
      <FlashCard card={mockCard} onFlip={jest.fn()} />
    );
    
    expect(getByText('What is React Native?')).toBeTruthy();
  });

  it('shows back side when flipped', async () => {
    const onFlip = jest.fn();
    const { getByText, getByTestId } = render(
      <FlashCard card={mockCard} onFlip={onFlip} />
    );
    
    const card = getByTestId('flashcard-container');
    fireEvent.press(card);
    
    await waitFor(() => {
      expect(onFlip).toHaveBeenCalledWith(true);
    });
  });

  it('displays difficulty indicator', () => {
    const { getByTestId } = render(
      <FlashCard card={mockCard} onFlip={jest.fn()} />
    );
    
    const difficultyIndicator = getByTestId('difficulty-indicator');
    expect(difficultyIndicator).toBeTruthy();
  });

  it('handles image hotspot cards', () => {
    const { getByTestId } = render(
      <FlashCard card={mockImageCard} onFlip={jest.fn()} />
    );
    
    const imageContainer = getByTestId('image-container');
    expect(imageContainer).toBeTruthy();
  });

  it('applies correct styling for different card types', () => {
    const { getByTestId } = render(
      <FlashCard card={mockCard} onFlip={jest.fn()} />
    );
    
    const cardContainer = getByTestId('flashcard-container');
    expect(cardContainer.props.style).toMatchObject(
      expect.objectContaining({
        backgroundColor: expect.any(String),
      })
    );
  });

  it('handles long text content properly', () => {
    const longTextCard: Card = {
      ...mockCard,
      front: 'This is a very long question that should wrap properly and not overflow the card boundaries. It contains multiple sentences and should be displayed correctly.',
    };

    const { getByText } = render(
      <FlashCard card={longTextCard} onFlip={jest.fn()} />
    );
    
    expect(getByText(longTextCard.front)).toBeTruthy();
  });

  it('supports accessibility features', () => {
    const { getByTestId } = render(
      <FlashCard card={mockCard} onFlip={jest.fn()} />
    );
    
    const cardContainer = getByTestId('flashcard-container');
    expect(cardContainer.props.accessible).toBe(true);
    expect(cardContainer.props.accessibilityRole).toBe('button');
  });
});