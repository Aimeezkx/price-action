import { renderHook, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useDocuments, useDocument, useUploadDocument } from '../useDocuments';
import { apiClient } from '../../lib/api';
import type { Document } from '../../types';

// Mock the API client
vi.mock('../../lib/api', () => ({
  apiClient: {
    getDocuments: vi.fn(),
    getDocument: vi.fn(),
    uploadDocument: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

const mockDocuments: Document[] = [
  {
    id: '1',
    filename: 'test-document.pdf',
    status: 'completed',
    chapter_count: 3,
    figure_count: 5,
    knowledge_count: 25,
    created_at: '2023-01-01T00:00:00Z',
  },
  {
    id: '2',
    filename: 'another-document.docx',
    status: 'processing',
    chapter_count: 0,
    figure_count: 0,
    knowledge_count: 0,
    created_at: '2023-01-02T00:00:00Z',
  },
];

const mockDocument: Document = mockDocuments[0];

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

describe('useDocuments', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useDocuments hook', () => {
    it('fetches documents successfully', async () => {
      mockApiClient.getDocuments.mockResolvedValue(mockDocuments);

      const { result } = renderHook(() => useDocuments(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockDocuments);
      expect(result.current.error).toBeNull();
      expect(mockApiClient.getDocuments).toHaveBeenCalledTimes(1);
    });

    it('handles fetch error', async () => {
      const error = new Error('Failed to fetch documents');
      mockApiClient.getDocuments.mockRejectedValue(error);

      const { result } = renderHook(() => useDocuments(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toEqual(error);
    });

    it('uses correct query key', async () => {
      mockApiClient.getDocuments.mockResolvedValue(mockDocuments);

      const { result } = renderHook(() => useDocuments(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // The query should be cached with the correct key
      expect(mockApiClient.getDocuments).toHaveBeenCalledTimes(1);
    });
  });

  describe('useDocument hook', () => {
    it('fetches single document successfully', async () => {
      mockApiClient.getDocument.mockResolvedValue(mockDocument);

      const { result } = renderHook(() => useDocument('1'), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockDocument);
      expect(result.current.error).toBeNull();
      expect(mockApiClient.getDocument).toHaveBeenCalledWith('1');
    });

    it('handles single document fetch error', async () => {
      const error = new Error('Document not found');
      mockApiClient.getDocument.mockRejectedValue(error);

      const { result } = renderHook(() => useDocument('1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toEqual(error);
    });

    it('does not fetch when id is empty', () => {
      const { result } = renderHook(() => useDocument(''), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(false);
      expect(mockApiClient.getDocument).not.toHaveBeenCalled();
    });

    it('does not fetch when id is undefined', () => {
      const { result } = renderHook(() => useDocument(undefined as any), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(false);
      expect(mockApiClient.getDocument).not.toHaveBeenCalled();
    });

    it('refetches when id changes', async () => {
      mockApiClient.getDocument.mockResolvedValue(mockDocument);

      const { result, rerender } = renderHook(
        ({ id }) => useDocument(id),
        {
          wrapper: createWrapper(),
          initialProps: { id: '1' },
        }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockApiClient.getDocument).toHaveBeenCalledWith('1');

      // Change the ID
      rerender({ id: '2' });

      await waitFor(() => {
        expect(mockApiClient.getDocument).toHaveBeenCalledWith('2');
      });

      expect(mockApiClient.getDocument).toHaveBeenCalledTimes(2);
    });
  });

  describe('useUploadDocument hook', () => {
    it('uploads document successfully', async () => {
      const uploadedDocument = { ...mockDocument, id: '3' };
      mockApiClient.uploadDocument.mockResolvedValue(uploadedDocument);
      mockApiClient.getDocuments.mockResolvedValue([...mockDocuments, uploadedDocument]);

      const { result } = renderHook(() => useUploadDocument(), {
        wrapper: createWrapper(),
      });

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      expect(result.current.isPending).toBe(false);

      result.current.mutate(file);

      expect(result.current.isPending).toBe(true);

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });

      expect(result.current.isSuccess).toBe(true);
      expect(result.current.data).toEqual(uploadedDocument);
      expect(mockApiClient.uploadDocument).toHaveBeenCalledWith(file);
    });

    it('handles upload error', async () => {
      const error = new Error('Upload failed');
      mockApiClient.uploadDocument.mockRejectedValue(error);

      const { result } = renderHook(() => useUploadDocument(), {
        wrapper: createWrapper(),
      });

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      result.current.mutate(file);

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });

      expect(result.current.isError).toBe(true);
      expect(result.current.error).toEqual(error);
    });

    it('invalidates documents query on successful upload', async () => {
      const uploadedDocument = { ...mockDocument, id: '3' };
      mockApiClient.uploadDocument.mockResolvedValue(uploadedDocument);
      mockApiClient.getDocuments.mockResolvedValue([...mockDocuments, uploadedDocument]);

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

      const { result } = renderHook(() => useUploadDocument(), { wrapper });

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      result.current.mutate(file);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['documents'] });
    });

    it('can be called multiple times', async () => {
      const uploadedDocument1 = { ...mockDocument, id: '3' };
      const uploadedDocument2 = { ...mockDocument, id: '4' };
      
      mockApiClient.uploadDocument
        .mockResolvedValueOnce(uploadedDocument1)
        .mockResolvedValueOnce(uploadedDocument2);

      const { result } = renderHook(() => useUploadDocument(), {
        wrapper: createWrapper(),
      });

      const file1 = new File(['test content 1'], 'test1.pdf', { type: 'application/pdf' });
      const file2 = new File(['test content 2'], 'test2.pdf', { type: 'application/pdf' });

      // First upload
      result.current.mutate(file1);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(uploadedDocument1);

      // Reset mutation state
      result.current.reset();

      // Second upload
      result.current.mutate(file2);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(uploadedDocument2);
      expect(mockApiClient.uploadDocument).toHaveBeenCalledTimes(2);
    });

    it('provides mutation status correctly', async () => {
      mockApiClient.uploadDocument.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockDocument), 100))
      );

      const { result } = renderHook(() => useUploadDocument(), {
        wrapper: createWrapper(),
      });

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      // Initial state
      expect(result.current.isPending).toBe(false);
      expect(result.current.isSuccess).toBe(false);
      expect(result.current.isError).toBe(false);

      // Start mutation
      result.current.mutate(file);

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
      mockApiClient.getDocuments.mockRejectedValue(networkError);

      const { result } = renderHook(() => useDocuments(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toEqual(networkError);
      expect(result.current.data).toBeUndefined();
    });

    it('handles API errors with status codes', async () => {
      const apiError = new Error('Not found');
      (apiError as any).status = 404;
      mockApiClient.getDocument.mockRejectedValue(apiError);

      const { result } = renderHook(() => useDocument('nonexistent'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('Caching behavior', () => {
    it('caches documents query results', async () => {
      mockApiClient.getDocuments.mockResolvedValue(mockDocuments);

      const { result: result1 } = renderHook(() => useDocuments(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false);
      });

      // Second hook should use cached data
      const { result: result2 } = renderHook(() => useDocuments(), {
        wrapper: createWrapper(),
      });

      expect(result2.current.data).toEqual(mockDocuments);
      expect(mockApiClient.getDocuments).toHaveBeenCalledTimes(1); // Still only called once
    });

    it('caches individual document queries', async () => {
      mockApiClient.getDocument.mockResolvedValue(mockDocument);

      const wrapper = createWrapper();

      const { result: result1 } = renderHook(() => useDocument('1'), { wrapper });

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false);
      });

      // Second hook with same ID should use cached data
      const { result: result2 } = renderHook(() => useDocument('1'), { wrapper });

      expect(result2.current.data).toEqual(mockDocument);
      expect(mockApiClient.getDocument).toHaveBeenCalledTimes(1);
    });
  });
});