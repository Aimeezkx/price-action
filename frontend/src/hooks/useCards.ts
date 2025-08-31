import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import type { Card } from '../types';

export function useCards(filters?: Record<string, string>) {
  return useQuery<Card[]>({
    queryKey: ['cards', filters],
    queryFn: async () => {
      return await apiClient.getCards(filters);
    },
  });
}

export function useTodayReview() {
  return useQuery<Card[]>({
    queryKey: ['review', 'today'],
    queryFn: async () => {
      return await apiClient.getTodayReview();
    },
  });
}

export function useGradeCard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ cardId, grade }: { cardId: string; grade: number }) => {
      return await apiClient.gradeCard(cardId, grade);
    },
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
    mutationFn: async (documentId: string) => {
      return await apiClient.generateCards(documentId);
    },
    onSuccess: () => {
      // Invalidate cards to refetch
      queryClient.invalidateQueries({ queryKey: ['cards'] });
    },
  });
}