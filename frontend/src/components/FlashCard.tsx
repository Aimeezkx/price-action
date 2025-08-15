import React, { useState, useEffect } from 'react';
import type { Card, Hotspot } from '../types';
import { ImageHotspotViewer } from './ImageHotspotViewer';

interface FlashCardProps {
  card: Card;
  isFlipped: boolean;
  onFlip: () => void;
  onHotspotValidation?: (correct: boolean) => void;
  className?: string;
}

export function FlashCard({ card, isFlipped, onFlip, onHotspotValidation, className = '' }: FlashCardProps) {
  const [isAnimating, setIsAnimating] = useState(false);
  const [hotspotValidated, setHotspotValidated] = useState(false);

  const handleFlip = () => {
    if (isAnimating) return;
    setIsAnimating(true);
    onFlip();
    setTimeout(() => setIsAnimating(false), 300);
  };

  const handleHotspotValidation = (correct: boolean, clickedHotspots: Hotspot[]) => {
    setHotspotValidated(true);
    onHotspotValidation?.(correct);
    
    // Auto-flip after validation
    setTimeout(() => {
      if (!isFlipped) {
        onFlip();
      }
    }, 1500);
  };

  const renderCardContent = (content: string, isBack: boolean = false) => {
    if (card.card_type === 'image_hotspot' && !isBack) {
      // Parse hotspots from metadata
      const hotspots: Hotspot[] = card.metadata?.hotspots || [];
      
      return (
        <div className="w-full h-full">
          <ImageHotspotViewer
            imageSrc={content.startsWith('/') ? `/api/files${content}` : content}
            hotspots={hotspots}
            mode={hotspotValidated ? 'answer' : 'study'}
            onValidationComplete={handleHotspotValidation}
            className="w-full h-full"
          />
        </div>
      );
    }

    if (card.card_type === 'cloze') {
      // Render cloze deletion with blanks
      const blanks = card.metadata?.blanks || [];
      let displayText = content;
      
      if (!isBack && blanks.length > 0) {
        blanks.forEach((blank: string, index: number) => {
          displayText = displayText.replace(blank, `[${index + 1}]`);
        });
      }

      return (
        <div className="prose prose-sm max-w-none">
          <p className="text-lg leading-relaxed">{displayText}</p>
        </div>
      );
    }

    return (
      <div className="prose prose-sm max-w-none">
        <p className="text-lg leading-relaxed">{content}</p>
      </div>
    );
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= 1.5) return 'bg-green-100 text-green-800';
    if (difficulty <= 2.5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getDifficultyLabel = (difficulty: number) => {
    if (difficulty <= 1.5) return 'Easy';
    if (difficulty <= 2.5) return 'Medium';
    return 'Hard';
  };

  return (
    <div className={`relative w-full max-w-2xl mx-auto ${className}`}>
      {/* Card container with flip animation */}
      <div
        className={`relative w-full h-96 cursor-pointer transition-transform duration-300 transform-style-preserve-3d ${
          isFlipped ? 'rotate-y-180' : ''
        }`}
        onClick={handleFlip}
      >
        {/* Front of card */}
        <div
          className={`absolute inset-0 w-full h-full backface-hidden ${
            isFlipped ? 'rotate-y-180' : ''
          }`}
        >
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 h-full p-6 flex flex-col">
            {/* Card header */}
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                  {card.card_type.replace('_', ' ')}
                </span>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDifficultyColor(
                    card.difficulty
                  )}`}
                >
                  {getDifficultyLabel(card.difficulty)}
                </span>
              </div>
              <div className="text-sm text-gray-400">
                Click to flip
              </div>
            </div>

            {/* Card content */}
            <div className="flex-1 flex items-center justify-center">
              {renderCardContent(card.front)}
            </div>

            {/* Card footer */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="flex justify-center">
                <svg
                  className="w-6 h-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Back of card */}
        <div
          className={`absolute inset-0 w-full h-full backface-hidden rotate-y-180 ${
            isFlipped ? '' : 'rotate-y-180'
          }`}
        >
          <div className="bg-blue-50 rounded-xl shadow-lg border border-blue-200 h-full p-6 flex flex-col">
            {/* Card header */}
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-blue-600 uppercase tracking-wide">
                  Answer
                </span>
              </div>
              <div className="text-sm text-blue-400">
                Grade your answer
              </div>
            </div>

            {/* Card content */}
            <div className="flex-1 flex items-center justify-center">
              {renderCardContent(card.back, true)}
            </div>

            {/* Card footer */}
            <div className="mt-4 pt-4 border-t border-blue-100">
              <div className="flex justify-center">
                <svg
                  className="w-6 h-6 text-blue-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}