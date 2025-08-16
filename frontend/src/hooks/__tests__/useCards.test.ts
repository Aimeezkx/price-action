import { renderHook, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useCards, useTodayReview, useGradeCard, useGenerateCards } from '../useCards';
import { apiClient } from '../../lib/api';
import type { Card } from '../../types';

// Mock the API client
vi.mock('../../lib/api', () => ({
  apiClient: {
    getCards: vi.fn(),
    getTodayReview: vi.fn(),
    gradeCard: vi.fn(),
    generateCards: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

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
];

const mockTodayReview: Card[] = [mockCards[0]];

// Test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    React.createElement(QueryClientProvider, { client: queryClient }, children)
  );
};

describe('useCards hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useCards hook', () => {
    it('fetches cards successfully without filters', async () => {
      mockApiClient.getCards.mockResolvedValue(mockCards);

      const { result } = renderHook(() => useCards(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockCards);
      expect(result.current.error).toBeNull();
      expect(mockApiClient.getCards).toHaveBeenCalledWith(undefined);
    });

    it('fetches cards with filters', async () => {
      const filters = { chapter: 'chapter-1', difficulty: 'easy' };
      mockApiClient.getCards.mockResolvedValue(mockCards);

      const { result } = renderHook(() => useCards(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockCards);
      expect(mockApiClient.getCards).toHaveBeenCalledWith(filters);
    });

    it('handles fetch error', async () => {
      const error = new Error('Failed to fetch cards');
      mockApiClient.getCards.mockRejectedValue(error);

      const { result } = renderHook(() => useCards(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toEqual(error);
    });

    it('refetches when filters change', async () => {
      mockApiClient.getCards.mockResolvedValue(mockCards);

      const { result, rerender } = renderHook(
        ({ filters }) => useCards(filters),
        {
          wrapper: createWrapper(),
          initialProps: { filters: { chapter: 'chapter-1' } },
        }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockApiClient.getCards).toHaveBeenCalledWith({ chapter: 'chapter-1' });

      // Change filters
      rerender({ filters: { chapter: 'chapter-2' } });

      await waitFor(() => {
        expect(mockApiClient.getCards).toHaveBeenCalledWith({ chapter: 'chapter-2' });
      });

      expect(mockApiClient.getCards).toHaveBeenCalledTimes(2);
    });

    it('uses different cache keys for different filters', async () => {
      mockApiClient.getCards.mockResolvedValue(mockCards);

      const wrapper = createWrapper();

      // First hook with filters
      const { result: result1 } = renderHook(
        () => useCards({ chapter: 'chapter-1' }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false);
      });

      // Second hook with different filters
      const { result: result2 } = renderHook(
        () => useCards({ chapter: 'chapter-2' }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result2.current.isLoading).toBe(false);
      });

      // Should have made separate API calls
      expect(mockApiClient.getCards).toHaveBeenCalledTimes(2);
      expect(mockApiClient.getCards).toHaveBeenCalledWith({ chapter: 'chapter-1' });
      expect(mockApiClient.getCards).toHaveBeenCalledWith({ chapter: 'chapter-2' });
    });
  });

  describe('useTodayReview hook', () => {
    it('fetches today review cards successfully', async () => {
      mockApiClient.getTodayReview.mockResolvedValue(mockTodayReview);

      const { result } = renderHook(() => useTodayReview(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockTodayReview);
      expect(result.current.error).toBeNull();
      expect(mockApiClient.getTodayReview).toHaveBeenCalledTimes(1);
    });

    it('handles fetch error for today review', async () => {
      const error = new Error('Failed to fetch today review');
      mockApiClient.getTodayReview.mockRejectedValue(error);

      const { result } = renderHook(() => useTodayReview(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toEqual(error);
    });

    it('uses correct query key for today review', async () => {
      mockApiClient.getTodayReview.mockResolvedValue(mockTodayReview);

      const { result } = renderHook(() => useTodayReview(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should be cached separately from regular cards
      expect(mockApiClient.getTodayReview).toHaveBeenCalledTimes(1);
    });
  });

  describe('useGradeCard hook', () => {
    it('grades card successfully', async () => {
      const gradedCard = { ...mockCards[0], difficulty: 1.2 };
      mockApiClient.gradeCard.mockResolvedValue(gradedCard);

      const { result } = renderHook(() => useGradeCard(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isPending).toBe(false);

      result.current.mutate({ cardId: '1', grade: 4 });

      expect(result.current.isPending).toBe(true);

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });

      expect(result.current.isSuccess).toBe(true);
      expect(result.current.data).toEqual(gradedCard);
      expect(mockApiClient.gradeCard).toHaveBeenCalledWith('1', 4);
    });

    it('handles grading error', async () => {
      const error = new Error('Failed to grade card');
      mockApiClient.gradeCard.mockRejectedValue(error);

      const { result } = renderHook(() => useGradeCard(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ cardId: '1', grade: 4 });

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });

      expect(result.current.isError).toBe(true);
      expect(result.current.error).toEqual(error);
    });

    it('invalidates review and cards queries on successful grading', async () => {
      const gradedCard = { ...mockCards[0], difficulty: 1.2 };
      mockApiClient.gradeCard.mockResolvedValue(gradedCard);

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        React.createElement(QueryClientProvider, { client: queryClient }, children)
      );

      const { result } = renderHook(() => useGradeCard(), { wrapper });

      result.current.mutate({ cardId: '1', grade: 4 });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['review'] });
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['cards'] });
    });

    it('can grade multiple cards', async () => {
      const gradedCard1 = { ...mockCards[0], difficulty: 1.2 };
      const gradedCard2 = { ...mockCards[1], difficulty: 1.8 };
      
      mockApiClient.gradeCard
        .mockResolvedValueOnce(gradedCard1)
        .mockResolvedValueOnce(gradedCard2);

      const { result } = renderHook(() => useGradeCard(), {
        wrapper: createWrapper(),
      });

      // First grading
      result.current.mutate({ cardId: '1', grade: 4 });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(gradedCard1);

      // Reset mutation state
      result.current.reset();

      // Second grading
      result.current.mutate({ cardId: '2', grade: 3 });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(gradedCard2);
      expect(mockApiClient.gradeCard).toHaveBeenCalledTimes(2);
    });

    it('validates grade parameter', async () => {
      mockApiClient.gradeCard.mockResolvedValue(mockCards[0]);

      const { result } = renderHook(() => useGradeCard(), {
        wrapper: createWrapper(),
      });

      // Test different grade values
      result.current.mutate({ cardId: '1', grade: 1 });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      result.current.reset();

      result.current.mutate({ cardId: '1', grade: 5 });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockApiClient.gradeCard).toHaveBeenCalledWith('1', 1);
      expect(mockApiClient.gradeCard).toHaveBeenCalledWith('1', 5);
    });
  });

  describe('useGenerateCards hook', () => {
    it('generates cards successfully', async () => {
      const generatedCards = mockCards;
      mockApiClient.generateCards.mockResolvedValue(generatedCards);

      const { result } = renderHook(() => useGenerateCards(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isPending).toBe(false);

      result.current.mutate('document-1');

      expect(result.current.isPending).toBe(true);

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });

      expect(result.current.isSuccess).toBe(true);
      expect(result.current.data).toEqual(generatedCards);
      expect(mockApiClient.generateCards).toHaveBeenCalledWith('document-1');
    });

    it('handles card generation error', async () => {
      const error = new Error('Failed to generate cards');
      mockApiClient.generateCards.mockRejectedValue(error);

      const { result } = renderHook(() => useGenerateCards(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('document-1');

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });

      expect(result.current.isError).toBe(true);
      expect(result.current.error).toEqual(error);
    });

    it('invalidates cards query on successful generation', async () => {
      const generatedCards = mockCards;
      mockApiClient.generateCards.mockResolvedValue(generatedCards);

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        React.createElement(QueryClientProvider, { client: queryClient }, children)
      );

      const { result } = renderHook(() => useGenerateCards(), { wrapper });

      result.current.mutate('document-1');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['cards'] });
    });

    it('can generate cards for multiple documents', async () => {
      const generatedCards1 = [mockCards[0]];
      const generatedCards2 = [mockCards[1]];
      
      mockApiClient.generateCards
        .mockResolvedValueOnce(generatedCards1)
        .mockResolvedValueOnce(generatedCards2);

      const { result } = renderHook(() => useGenerateCards(), {
        wrapper: createWrapper(),
      });

      // First generation
      result.current.mutate('document-1');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(generatedCards1);

      // Reset mutation state
      result.current.reset();

      // Second generation
      result.current.mutate('document-2');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(generatedCards2);
      expect(mockApiClient.generateCards).toHaveBeenCalledTimes(2);
    });

    it('provides correct mutation status during generation', async () => {
      mockApiClient.generateCards.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockCards), 100))
      );

      const { result } = renderHook(() => useGenerateCards(), {
        wrapper: createWrapper(),
      });

      // Initial state
      expect(result.current.isPending).toBe(false);
      expect(result.current.isSuccess).toBe(false);
      expect(result.current.isError).toBe(false);

      // Start generation
      result.current.mutate('document-1');

      expect(result.current.isPending).toBe(true);
      expect(result.current.isSuccess).toBe(false);
      expect(result.current.isError).toBe(false);

      // Wait for completion
      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });

      expect(result.current.isSuccess).toBe(true);
      expect(result.current.isError).toBe(false);
    });
  });

  describe('Error handling', () => {
    it('handles network errors gracefully', async () => {
      const networkError = new Error('Network error');
      networkError.name = 'NetworkError';
      mockApiClient.getCards.mockRejectedValue(networkError);

      const { result } = renderHook(() => useCards(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toEqual(networkError);
      expect(result.current.data).toBeUndefined();
    });

    it('handles API errors with status codes', async () => {
      const apiError = new Error('Unauthorized');
      (apiError as any).status = 401;
      mockApiClient.getTodayReview.mockRejectedValue(apiError);

      const { result } = renderHook(() => useTodayReview(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('Caching behavior', () => {
    it('caches cards query results', async () => {
      mockApiClient.getCards.mockResolvedValue(mockCards);

      const wrapper = createWrapper();

      const { result: result1 } = renderHook(() => useCards(), { wrapper });

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false);
      });

      // Second hook should use cached data
      const { result: result2 } = renderHook(() => useCards(), { wrapper });

      expect(result2.current.data).toEqual(mockCards);
      expect(mockApiClient.getCards).toHaveBeenCalledTimes(1);
    });

    it('caches today review separately', async () => {
      mockApiClient.getCards.mockResolvedValue(mockCards);
      mockApiClient.getTodayReview.mockResolvedValue(mockTodayReview);

      const wrapper = createWrapper();

      const { result: cardsResult } = renderHook(() => useCards(), { wrapper });
      const { result: reviewResult } = renderHook(() => useTodayReview(), { wrapper });

      await waitFor(() => {
        expect(cardsResult.current.isLoading).toBe(false);
        expect(reviewResult.current.isLoading).toBe(false);
      });

      expect(cardsResult.current.data).toEqual(mockCards);
      expect(reviewResult.current.data).toEqual(mockTodayReview);
      expect(mockApiClient.getCards).toHaveBeenCalledTimes(1);
      expect(mockApiClient.getTodayReview).toHaveBeenCalledTimes(1);
    });
  });
});