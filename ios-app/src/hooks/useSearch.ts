import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import type { SearchResult } from '../types';

export function useSearch(query?: string, filters?: Record<string, string>) {
  return useQuery<SearchResult[]>({
    queryKey: ['search', query, filters],
    queryFn: () => apiClient.search(query!, filters),
    enabled: !!query && query.trim().length > 0,
  });
}