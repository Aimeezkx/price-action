import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import type { Card } from '../types';

export function useCards(filters?: Record<string, string>) {
  return useQuery<Card[]>({
    queryKey: ['cards', filters],
    queryFn: () => apiClient.getCards(filters),
  });
}

export function useTodayReview() {
  return useQuery<Card[]>({
    queryKey: ['review', 'today'],
    queryFn: () => apiClient.getTodayReview(),
  });
}

export function useGradeCard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cardId, grade }: { cardId: string; grade: number }) =>
      apiClient.gradeCard(cardId, grade),
    onSuccess: () => {
      // Invalidate review queries to refetch
      queryClient.invalidateQueries({ queryKey: ['review'] });
      queryClient.invalidateQueries({ queryKey: ['cards'] });
    },
  });
}

export function useGenerateCards() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => apiClient.generateCards(documentId),
    onSuccess: () => {
      // Invalidate cards to refetch
      queryClient.invalidateQueries({ queryKey: ['cards'] });
    },
  });
}