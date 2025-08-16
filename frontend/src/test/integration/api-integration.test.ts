/**
 * Frontend-Backend API Integration Tests
 * Tests the complete integration between frontend and backend APIs
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

import { DocumentUpload } from '../../components/DocumentUpload';
import { DocumentList } from '../../components/DocumentList';
import { SearchInput } from '../../components/SearchInput';
import { SearchResults } from '../../components/SearchResults';
import { FlashCard } from '../../components/FlashCard';
import { api } from '../../lib/api';

// Mock server for API integration testing
const server = setupServer(
  // Document upload endpoint
  rest.post('/api/documents/upload', (req, res, ctx) => {
    return res(
      ctx.json({
        document_id: 'test-doc-123',
        filename: 'test.pdf',
        status: 'uploaded'
      })
    );
  }),

  // Document list endpoint
  rest.get('/api/documents', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'test-doc-123',
          filename: 'test.pdf',
          status: 'completed',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        },
        {
          id: 'test-doc-456',
          filename: 'another.pdf',
          status: 'processing',
          created_at: '2024-01-01T01:00:00Z',
          updated_at: '2024-01-01T01:00:00Z'
        }
      ])
    );
  }),

  // Document details endpoint
  rest.get('/api/documents/:id', (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.json({
        id,
        filename: 'test.pdf',
        status: 'completed',
        content_text: 'Sample document content',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      })
    );
  }),

  // Search endpoint
  rest.get('/api/search', (req, res, ctx) => {
    const query = req.url.searchParams.get('query');
    return res(
      ctx.json({
        results: [
          {
            id: 'result-1',
            content: `Search result for "${query}"`,
            document_id: 'test-doc-123',
            chapter_id: 'chapter-1',
            relevance_score: 0.95
          },
          {
            id: 'result-2',
            content: `Another result for "${query}"`,
            document_id: 'test-doc-456',
            chapter_id: 'chapter-2',
            relevance_score: 0.87
          }
        ],
        total: 2
      })
    );
  }),

  // Cards endpoint
  rest.get('/api/cards/due', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'card-1',
          front_content: 'What is machine learning?',
          back_content: 'A subset of AI that focuses on algorithms',
          card_type: 'basic',
          knowledge_point_id: 'kp-1',
          due_date: '2024-01-01T00:00:00Z'
        },
        {
          id: 'card-2',
          front_content: 'Define neural network',
          back_content: 'A computing system inspired by biological neural networks',
          card_type: 'basic',
          knowledge_point_id: 'kp-2',
          due_date: '2024-01-01T01:00:00Z'
        }
      ])
    );
  }),

  // Card review endpoint
  rest.post('/api/cards/:id/review', (req, res, ctx) => {
    return res(
      ctx.json({
        next_due_date: '2024-01-02T00:00:00Z',
        new_interval: 2,
        ease_factor: 2.5
      })
    );
  })
);

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Frontend-Backend API Integration', () => {
  beforeEach(() => {
    server.listen();
  });

  afterEach(() => {
    server.resetHandlers();
  });

  describe('Document Upload Integration', () => {
    it('should upload document and show success message', async () => {
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      // Create a mock file
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      // Find file input and upload file
      const fileInput = screen.getByLabelText(/upload/i);
      fireEvent.change(fileInput, { target: { files: [file] } });

      // Click upload button
      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      // Wait for success message
      await waitFor(() => {
        expect(screen.getByText(/uploaded successfully/i)).toBeInTheDocument();
      });
    });

    it('should handle upload errors gracefully', async () => {
      // Mock error response
      server.use(
        rest.post('/api/documents/upload', (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({ detail: 'Invalid file type' })
          );
        })
      );

      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const file = new File(['test'], 'test.txt', { type: 'text/plain' });
      const fileInput = screen.getByLabelText(/upload/i);
      
      fireEvent.change(fileInput, { target: { files: [file] } });
      fireEvent.click(screen.getByRole('button', { name: /upload/i }));

      await waitFor(() => {
        expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
      });
    });
  });

  describe('Document List Integration', () => {
    it('should fetch and display documents', async () => {
      render(
        <TestWrapper>
          <DocumentList />
        </TestWrapper>
      );

      // Wait for documents to load
      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
        expect(screen.getByText('another.pdf')).toBeInTheDocument();
      });

      // Check status indicators
      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('processing')).toBeInTheDocument();
    });

    it('should handle empty document list', async () => {
      server.use(
        rest.get('/api/documents', (req, res, ctx) => {
          return res(ctx.json([]));
        })
      );

      render(
        <TestWrapper>
          <DocumentList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/no documents/i)).toBeInTheDocument();
      });
    });
  });

  describe('Search Integration', () => {
    it('should perform search and display results', async () => {
      render(
        <TestWrapper>
          <div>
            <SearchInput />
            <SearchResults />
          </div>
        </TestWrapper>
      );

      // Enter search query
      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: 'machine learning' } });
      fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter' });

      // Wait for search results
      await waitFor(() => {
        expect(screen.getByText(/search result for "machine learning"/i)).toBeInTheDocument();
        expect(screen.getByText(/another result for "machine learning"/i)).toBeInTheDocument();
      });
    });

    it('should handle search errors', async () => {
      server.use(
        rest.get('/api/search', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ detail: 'Search service unavailable' })
          );
        })
      );

      render(
        <TestWrapper>
          <div>
            <SearchInput />
            <SearchResults />
          </div>
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText(/search/i);
      fireEvent.change(searchInput, { target: { value: 'test query' } });
      fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter' });

      await waitFor(() => {
        expect(screen.getByText(/search service unavailable/i)).toBeInTheDocument();
      });
    });
  });

  describe('Card Review Integration', () => {
    it('should load and review cards', async () => {
      render(
        <TestWrapper>
          <FlashCard />
        </TestWrapper>
      );

      // Wait for card to load
      await waitFor(() => {
        expect(screen.getByText('What is machine learning?')).toBeInTheDocument();
      });

      // Flip card to see answer
      const flipButton = screen.getByRole('button', { name: /flip/i });
      fireEvent.click(flipButton);

      await waitFor(() => {
        expect(screen.getByText('A subset of AI that focuses on algorithms')).toBeInTheDocument();
      });

      // Grade the card
      const gradeButton = screen.getByRole('button', { name: /good/i });
      fireEvent.click(gradeButton);

      // Should load next card or show completion
      await waitFor(() => {
        expect(screen.getByText(/next card|review complete/i)).toBeInTheDocument();
      });
    });
  });

  describe('API Error Handling', () => {
    it('should handle network errors', async () => {
      // Simulate network error
      server.use(
        rest.get('/api/documents', (req, res, ctx) => {
          return res.networkError('Network error');
        })
      );

      render(
        <TestWrapper>
          <DocumentList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/network error|connection failed/i)).toBeInTheDocument();
      });
    });

    it('should handle server errors', async () => {
      server.use(
        rest.get('/api/documents', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ detail: 'Internal server error' })
          );
        })
      );

      render(
        <TestWrapper>
          <DocumentList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/server error|something went wrong/i)).toBeInTheDocument();
      });
    });
  });

  describe('Real API Integration', () => {
    // These tests would run against actual backend (when available)
    it.skip('should integrate with real backend API', async () => {
      // This test would be enabled when running against real backend
      const response = await api.get('/api/health');
      expect(response.status).toBe(200);
    });

    it.skip('should handle real authentication flow', async () => {
      // Test real authentication integration
      const loginResponse = await api.post('/api/auth/login', {
        username: 'test@example.com',
        password: 'testpassword'
      });
      
      expect(loginResponse.data.access_token).toBeDefined();
    });
  });

  describe('Performance Integration', () => {
    it('should handle large document lists efficiently', async () => {
      // Mock large document list
      const largeDocumentList = Array.from({ length: 100 }, (_, i) => ({
        id: `doc-${i}`,
        filename: `document-${i}.pdf`,
        status: 'completed',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }));

      server.use(
        rest.get('/api/documents', (req, res, ctx) => {
          return res(ctx.json(largeDocumentList));
        })
      );

      const startTime = performance.now();

      render(
        <TestWrapper>
          <DocumentList />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('document-0.pdf')).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time (adjust threshold as needed)
      expect(renderTime).toBeLessThan(1000); // 1 second
    });

    it('should handle rapid search queries', async () => {
      render(
        <TestWrapper>
          <div>
            <SearchInput />
            <SearchResults />
          </div>
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText(/search/i);

      // Simulate rapid typing
      const queries = ['m', 'ma', 'mac', 'mach', 'machine'];
      
      for (const query of queries) {
        fireEvent.change(searchInput, { target: { value: query } });
        await new Promise(resolve => setTimeout(resolve, 50)); // 50ms delay
      }

      // Should handle debouncing and not crash
      await waitFor(() => {
        expect(searchInput).toHaveValue('machine');
      });
    });
  });
});