import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import type { Document } from '../types';

export function useDocuments() {
  return useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      return await apiClient.getDocuments();
    },
    refetchInterval: (documents) =>
      documents?.some((document) =>
        ['pending', 'processing', 'parsing', 'extracting', 'generating_cards'].includes(document.status)
      )
        ? 2000
        : false,
    refetchOnWindowFocus: true,
  });
}

export function useDocument(id: string) {
  return useQuery<Document>({
    queryKey: ['documents', id],
    queryFn: async () => {
      return await apiClient.getDocument(id);
    },
    enabled: !!id,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      return await apiClient.uploadDocument(file);
    },
    onSuccess: () => {
      // Invalidate documents list to refetch
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}
