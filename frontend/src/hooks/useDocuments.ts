import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import type { Document } from '../types';

export function useDocuments() {
  return useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: () => apiClient.getDocuments(),
  });
}

export function useDocument(id: string) {
  return useQuery<Document>({
    queryKey: ['documents', id],
    queryFn: () => apiClient.getDocument(id),
    enabled: !!id,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => apiClient.uploadDocument(file),
    onSuccess: () => {
      // Invalidate documents list to refetch
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}