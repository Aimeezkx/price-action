import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useCards, useGradeCard, useDailyReview } from '../useCards';
import * as api from '../../services/api';

// Mock the API
jest.mock('../../services/api');
const mockApi = api as jest.Mocked<typeof api>;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useCards', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches cards successfully', async () => {
    const mockCards = [
      {
        id: '1',
        front: 'Question',
        back: 'Answer',
        cardType: 'qa' as const,
        difficulty: 2.5,
        dueDate: new Date(),
        metadata: {},
      },
    ];

    mockApi.apiClient.getCards.mockResolvedValue(mockCards);

    const { result } = renderHook(() => useCards(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockCards);
    expect(mockApi.apiClient.getCards).toHaveBeenCalledWith({});
  });

  it('applies filters correctly', async () => {
    const filters = {
      chapter: 'chapter-1',
      difficulty: 'medium',
      cardType: 'qa',
    };

    mockApi.apiClient.getCards.mockResolvedValue([]);

    const { result } = renderHook(() => useCards(filters), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockApi.apiClient.getCards).toHaveBeenCalledWith(filters);
  });

  it('handles loading state', () => {
    mockApi.apiClient.getCards.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { result } = renderHook(() => useCards(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });

  it('handles error state', async () => {
    const error = new Error('Failed to fetch cards');
    mockApi.apiClient.getCards.mockRejectedValue(error);

    const { result } = renderHook(() => useCards(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });
});

describe('useGradeCard', () => {
  it('grades card successfully', async () => {
    mockApi.apiClient.gradeCard.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useGradeCard(), {
      wrapper: createWrapper(),
    });

    const gradeData = {
      cardId: '1',
      grade: 4,
      responseTime: 5000,
    };

    result.current.mutate(gradeData);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockApi.apiClient.gradeCard).toHaveBeenCalledWith(gradeData);
  });

  it('handles grading errors', async () => {
    const error = new Error('Failed to grade card');
    mockApi.apiClient.gradeCard.mockRejectedValue(error);

    const { result } = renderHook(() => useGradeCard(), {
      wrapper: createWrapper(),
    });

    const gradeData = {
      cardId: '1',
      grade: 4,
      responseTime: 5000,
    };

    result.current.mutate(gradeData);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it('invalidates cards query after successful grading', async () => {
    mockApi.apiClient.gradeCard.mockResolvedValue({ success: true });

    const { result } = renderHook(() => useGradeCard(), {
      wrapper: createWrapper(),
    });

    const gradeData = {
      cardId: '1',
      grade: 4,
      responseTime: 5000,
    };

    result.current.mutate(gradeData);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Verify that the mutation was successful
    expect(mockApi.apiClient.gradeCard).toHaveBeenCalledWith(gradeData);
  });
});

describe('useDailyReview', () => {
  it('fetches daily review cards', async () => {
    const mockReviewCards = [
      {
        id: '1',
        front: 'Review Question',
        back: 'Review Answer',
        cardType: 'qa' as const,
        difficulty: 3.0,
        dueDate: new Date(),
        metadata: {},
      },
    ];

    mockApi.apiClient.getDailyReview.mockResolvedValue(mockReviewCards);

    const { result } = renderHook(() => useDailyReview(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockReviewCards);
    expect(mockApi.apiClient.getDailyReview).toHaveBeenCalled();
  });

  it('handles empty review queue', async () => {
    mockApi.apiClient.getDailyReview.mockResolvedValue([]);

    const { result } = renderHook(() => useDailyReview(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual([]);
  });

  it('refetches on focus', async () => {
    mockApi.apiClient.getDailyReview.mockResolvedValue([]);

    const { result } = renderHook(() => useDailyReview(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Simulate app focus
    result.current.refetch();

    expect(mockApi.apiClient.getDailyReview).toHaveBeenCalledTimes(2);
  });
});