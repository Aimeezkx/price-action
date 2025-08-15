import React, { useState, useEffect, useCallback } from 'react';
import { FlashCard } from './FlashCard';
import { GradingInterface } from './GradingInterface';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';
import { useGradeCard } from '../hooks/useCards';
import type { Card } from '../types';

interface ReviewSessionProps {
  cards: Card[];
  onSessionComplete: () => void;
  onSessionExit: () => void;
}

export function ReviewSession({ cards, onSessionComplete, onSessionExit }: ReviewSessionProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [reviewedCards, setReviewedCards] = useState<Set<string>>(new Set());
  const [sessionStats, setSessionStats] = useState({
    total: cards.length,
    reviewed: 0,
    correct: 0,
    startTime: Date.now(),
  });

  const gradeCardMutation = useGradeCard();
  const currentCard = cards[currentIndex];
  const isLastCard = currentIndex === cards.length - 1;
  const allCardsReviewed = reviewedCards.size === cards.length;

  // Keyboard shortcuts
  const handleKeyPress = useCallback((event: KeyboardEvent) => {
    if (gradeCardMutation.isPending) return;

    switch (event.key) {
      case ' ':
        event.preventDefault();
        if (!isFlipped) {
          setIsFlipped(true);
        }
        break;
      case 'j':
      case 'ArrowDown':
        event.preventDefault();
        if (currentIndex < cards.length - 1) {
          setCurrentIndex(currentIndex + 1);
          setIsFlipped(false);
        }
        break;
      case 'k':
      case 'ArrowUp':
        event.preventDefault();
        if (currentIndex > 0) {
          setCurrentIndex(currentIndex - 1);
          setIsFlipped(false);
        }
        break;
      case '0':
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
        if (isFlipped) {
          const grade = parseInt(event.key, 10);
          handleGrade(grade);
        }
        break;
      case 'Escape':
        onSessionExit();
        break;
    }
  }, [currentIndex, isFlipped, cards.length, gradeCardMutation.isPending, onSessionExit]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);

  const handleFlip = () => {
    if (!gradeCardMutation.isPending) {
      setIsFlipped(!isFlipped);
    }
  };

  const handleGrade = async (grade: number) => {
    if (!currentCard || gradeCardMutation.isPending) return;

    try {
      await gradeCardMutation.mutateAsync({ cardId: currentCard.id, grade });
      
      // Update stats
      const wasCorrect = grade >= 3;
      setReviewedCards(prev => new Set([...prev, currentCard.id]));
      setSessionStats(prev => ({
        ...prev,
        reviewed: prev.reviewed + 1,
        correct: prev.correct + (wasCorrect ? 1 : 0),
      }));

      // Move to next card or complete session
      if (isLastCard) {
        onSessionComplete();
      } else {
        setCurrentIndex(currentIndex + 1);
        setIsFlipped(false);
      }
    } catch (error) {
      console.error('Failed to grade card:', error);
    }
  };

  const handleNavigation = (direction: 'prev' | 'next') => {
    if (gradeCardMutation.isPending) return;

    if (direction === 'prev' && currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setIsFlipped(false);
    } else if (direction === 'next' && currentIndex < cards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsFlipped(false);
    }
  };

  const getProgressPercentage = () => {
    return Math.round((sessionStats.reviewed / sessionStats.total) * 100);
  };

  const getAccuracyPercentage = () => {
    if (sessionStats.reviewed === 0) return 0;
    return Math.round((sessionStats.correct / sessionStats.reviewed) * 100);
  };

  if (!currentCard) {
    return (
      <div className="flex justify-center items-center h-64">
        <ErrorMessage message="No cards available for review" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Session Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Review Session</h1>
              <p className="text-sm text-gray-600">
                Card {currentIndex + 1} of {cards.length}
              </p>
            </div>
            <button
              onClick={onSessionExit}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Exit Session
            </button>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getProgressPercentage()}%` }}
            />
          </div>

          {/* Session Stats */}
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-white rounded-lg p-3 shadow-sm">
              <div className="text-2xl font-bold text-blue-600">{getProgressPercentage()}%</div>
              <div className="text-sm text-gray-600">Progress</div>
            </div>
            <div className="bg-white rounded-lg p-3 shadow-sm">
              <div className="text-2xl font-bold text-green-600">{getAccuracyPercentage()}%</div>
              <div className="text-sm text-gray-600">Accuracy</div>
            </div>
            <div className="bg-white rounded-lg p-3 shadow-sm">
              <div className="text-2xl font-bold text-gray-900">{sessionStats.reviewed}</div>
              <div className="text-sm text-gray-600">Reviewed</div>
            </div>
          </div>
        </div>

        {/* Navigation Controls */}
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={() => handleNavigation('prev')}
            disabled={currentIndex === 0 || gradeCardMutation.isPending}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Previous (K)
          </button>

          <div className="text-sm text-gray-500">
            Press <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">Space</kbd> to flip
          </div>

          <button
            onClick={() => handleNavigation('next')}
            disabled={currentIndex === cards.length - 1 || gradeCardMutation.isPending}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Next (J)
            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Flash Card */}
        <div className="mb-8">
          <FlashCard
            card={currentCard}
            isFlipped={isFlipped}
            onFlip={handleFlip}
          />
        </div>

        {/* Grading Interface - Only show when card is flipped */}
        {isFlipped && (
          <div className="mb-8">
            <GradingInterface
              onGrade={handleGrade}
              disabled={gradeCardMutation.isPending}
            />
          </div>
        )}

        {/* Loading State */}
        {gradeCardMutation.isPending && (
          <div className="flex justify-center items-center py-4">
            <LoadingSpinner size="sm" />
            <span className="ml-2 text-sm text-gray-600">Saving your grade...</span>
          </div>
        )}

        {/* Error State */}
        {gradeCardMutation.error && (
          <div className="mb-4">
            <ErrorMessage
              message="Failed to save your grade. Please try again."
              onRetry={() => gradeCardMutation.reset()}
            />
          </div>
        )}
      </div>
    </div>
  );
}