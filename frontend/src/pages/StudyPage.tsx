import React, { useState } from 'react';
import { useTodayReview, useCards } from '../hooks/useCards';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { ReviewSession } from '../components/ReviewSession';
import { CardFilters, type CardFilters as CardFiltersType } from '../components/CardFilters';
import type { Card } from '../types';

export function StudyPage() {
  const [activeSession, setActiveSession] = useState<'today' | 'filtered' | null>(null);
  const [filters, setFilters] = useState<CardFiltersType>({});
  
  const { data: reviewCards, isLoading: reviewLoading, error: reviewError, refetch: refetchReview } = useTodayReview();
  
  // Build filter params for API
  const filterParams: Record<string, string> = {};
  if (filters.chapter) filterParams.chapter_id = filters.chapter;
  if (filters.cardType) filterParams.card_type = filters.cardType;
  if (filters.difficulty) {
    if (filters.difficulty === 'easy') {
      filterParams.max_difficulty = '1.5';
    } else if (filters.difficulty === 'medium') {
      filterParams.min_difficulty = '1.5';
      filterParams.max_difficulty = '2.5';
    } else if (filters.difficulty === 'hard') {
      filterParams.min_difficulty = '2.5';
    }
  }
  
  const { data: filteredCards, isLoading: filteredLoading, error: filteredError, refetch: refetchFiltered } = useCards(
    Object.keys(filterParams).length > 0 ? filterParams : undefined
  );

  const isLoading = reviewLoading || filteredLoading;
  const error = reviewError || filteredError;

  // Handle active review session
  if (activeSession === 'today' && reviewCards && reviewCards.length > 0) {
    return (
      <ReviewSession
        cards={reviewCards}
        onSessionComplete={() => {
          setActiveSession(null);
          refetchReview();
        }}
        onSessionExit={() => setActiveSession(null)}
      />
    );
  }

  if (activeSession === 'filtered' && filteredCards && filteredCards.length > 0) {
    return (
      <ReviewSession
        cards={filteredCards}
        onSessionComplete={() => {
          setActiveSession(null);
          refetchFiltered();
        }}
        onSessionExit={() => setActiveSession(null)}
      />
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load cards"
        onRetry={() => {
          refetchReview();
          refetchFiltered();
        }}
      />
    );
  }

  const reviewCardCount = reviewCards?.length || 0;
  const filteredCardCount = filteredCards?.length || 0;
  const hasFilters = Object.keys(filterParams).length > 0;

  return (
    <div>
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Study Session</h1>
          <p className="mt-2 text-sm text-gray-700">
            Review your flashcards using spaced repetition
          </p>
        </div>
      </div>

      {/* Today's Review Section */}
      <div className="mt-8">
        {reviewCardCount === 0 ? (
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="text-center">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No cards due today</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Great job! You're all caught up with your reviews.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="text-center">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Today's Review
                </h3>
                <div className="mt-2 max-w-xl text-sm text-gray-500">
                  <p>You have {reviewCardCount} cards due for review today.</p>
                </div>
                <div className="mt-5">
                  <button
                    onClick={() => setActiveSession('today')}
                    className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Start Review Session
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Card Filters Section */}
      <div className="mt-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Practice with Custom Filters</h2>
        <CardFilters
          filters={filters}
          onFiltersChange={setFilters}
          className="mb-6"
        />
        
        {hasFilters && (
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="text-center">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Filtered Practice
                </h3>
                <div className="mt-2 max-w-xl text-sm text-gray-500">
                  <p>
                    {filteredLoading 
                      ? 'Loading filtered cards...' 
                      : `Found ${filteredCardCount} cards matching your filters.`
                    }
                  </p>
                </div>
                {filteredCardCount > 0 && (
                  <div className="mt-5">
                    <button
                      onClick={() => setActiveSession('filtered')}
                      disabled={filteredLoading}
                      className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Start Filtered Practice
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Statistics Section */}
      <div className="mt-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Card Statistics</h2>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg
                    className="h-6 w-6 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Q&A Cards Due
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {reviewCards?.filter((card: Card) => card.card_type === 'qa').length || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg
                    className="h-6 w-6 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Cloze Cards Due
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {reviewCards?.filter((card: Card) => card.card_type === 'cloze').length || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg
                    className="h-6 w-6 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Image Cards Due
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {reviewCards?.filter((card: Card) => card.card_type === 'image_hotspot').length || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}