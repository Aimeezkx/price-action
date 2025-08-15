import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import type { TableOfContents, Knowledge } from '../types';

export function useTableOfContents(documentId: string) {
  return useQuery<TableOfContents>({
    queryKey: ['toc', documentId],
    queryFn: () => apiClient.getChapters(documentId),
    enabled: !!documentId,
  });
}

export function useChapterFigures(chapterId: string) {
  return useQuery({
    queryKey: ['chapter-figures', chapterId],
    queryFn: () => apiClient.getChapterFigures(chapterId),
    enabled: !!chapterId,
  });
}

export function useChapterKnowledge(
  chapterId: string,
  options?: {
    knowledge_type?: string;
    limit?: number;
    offset?: number;
  }
) {
  return useQuery<{
    chapter_id: string;
    chapter_title: string;
    total_knowledge_points: number;
    knowledge_points: Knowledge[];
  }>({
    queryKey: ['chapter-knowledge', chapterId, options],
    queryFn: () => apiClient.getChapterKnowledge(chapterId, options),
    enabled: !!chapterId,
  });
}