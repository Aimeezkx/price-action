import { apiClient, ApiError } from '../api';
import { Document, Card, Chapter } from '../../types';

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('Document API', () => {
    it('fetches documents successfully', async () => {
      const mockDocuments: Document[] = [
        {
          id: '1',
          filename: 'test.pdf',
          status: 'completed',
          chapterCount: 5,
          figureCount: 10,
          knowledgeCount: 25,
          createdAt: new Date(),
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockDocuments,
      } as Response);

      const result = await apiClient.getDocuments();
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/documents'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockDocuments);
    });

    it('uploads document with progress tracking', async () => {
      const mockFile = {
        uri: 'file://test.pdf',
        type: 'application/pdf',
        name: 'test.pdf',
      };

      const mockResponse = {
        id: '1',
        filename: 'test.pdf',
        status: 'processing',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const onProgress = jest.fn();
      const result = await apiClient.uploadDocument(mockFile, onProgress);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/ingest'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('handles upload errors gracefully', async () => {
      const mockFile = {
        uri: 'file://test.pdf',
        type: 'application/pdf',
        name: 'test.pdf',
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 413,
        json: async () => ({ error: 'File too large' }),
      } as Response);

      await expect(apiClient.uploadDocument(mockFile)).rejects.toThrow(ApiError);
    });
  });

  describe('Cards API', () => {
    it('fetches cards with filters', async () => {
      const mockCards: Card[] = [
        {
          id: '1',
          front: 'Question',
          back: 'Answer',
          cardType: 'qa',
          difficulty: 2.5,
          dueDate: new Date(),
          metadata: {},
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCards,
      } as Response);

      const filters = {
        chapter: 'chapter-1',
        difficulty: 'medium',
        cardType: 'qa',
      };

      const result = await apiClient.getCards(filters);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/cards'),
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockCards);
    });

    it('submits card grades correctly', async () => {
      const gradeData = {
        cardId: '1',
        grade: 4,
        responseTime: 5000,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response);

      await apiClient.gradeCard(gradeData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/review/grade'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(gradeData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('fetches daily review cards', async () => {
      const mockReviewCards: Card[] = [
        {
          id: '1',
          front: 'Review Question',
          back: 'Review Answer',
          cardType: 'qa',
          difficulty: 3.0,
          dueDate: new Date(),
          metadata: {},
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockReviewCards,
      } as Response);

      const result = await apiClient.getDailyReview();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/review/today'),
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockReviewCards);
    });
  });

  describe('Search API', () => {
    it('performs text search with highlighting', async () => {
      const mockResults = {
        cards: [
          {
            id: '1',
            front: 'Machine <mark>learning</mark> question',
            back: 'Answer about ML',
            cardType: 'qa',
            difficulty: 2.5,
            dueDate: new Date(),
            metadata: {},
          },
        ],
        total: 1,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResults,
      } as Response);

      const result = await apiClient.searchCards('learning', {
        type: 'text',
        filters: { chapter: 'ml-basics' },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/search'),
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockResults);
    });

    it('performs semantic search', async () => {
      const mockResults = {
        cards: [
          {
            id: '1',
            front: 'Neural network question',
            back: 'Deep learning answer',
            cardType: 'qa',
            difficulty: 3.5,
            dueDate: new Date(),
            metadata: {},
          },
        ],
        total: 1,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResults,
      } as Response);

      const result = await apiClient.searchCards('artificial intelligence', {
        type: 'semantic',
        threshold: 0.8,
      });

      expect(result).toEqual(mockResults);
    });
  });

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.getDocuments()).rejects.toThrow('Network error');
    });

    it('handles HTTP error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ error: 'Not found' }),
      } as Response);

      await expect(apiClient.getDocuments()).rejects.toThrow(ApiError);
    });

    it('handles malformed JSON responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      } as Response);

      await expect(apiClient.getDocuments()).rejects.toThrow('Invalid JSON');
    });
  });

  describe('Request Retry Logic', () => {
    it('retries failed requests up to 3 times', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        } as Response);

      const result = await apiClient.getDocuments();

      expect(mockFetch).toHaveBeenCalledTimes(3);
      expect(result).toEqual([]);
    });

    it('gives up after 3 failed attempts', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.getDocuments()).rejects.toThrow('Network error');
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });
  });
});