import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../../test/utils';
import { vi } from 'vitest';
import { DocumentList } from '../DocumentList';
import type { Document } from '../../types';

// Mock the hooks
vi.mock('../../hooks/useDocuments', () => ({
  useDocuments: vi.fn(),
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    Link: ({ to, children, onClick, ...props }: any) => (
      <a href={to} onClick={onClick} {...props}>
        {children}
      </a>
    ),
  };
});

// Mock child components
vi.mock('../LoadingSpinner', () => ({
  LoadingSpinner: ({ size }: { size: string }) => (
    <div data-testid="loading-spinner" data-size={size}>Loading...</div>
  ),
}));

vi.mock('../ErrorMessage', () => ({
  ErrorMessage: ({ message, onRetry }: { message: string; onRetry: () => void }) => (
    <div data-testid="error-message">
      <span>{message}</span>
      <button onClick={onRetry} data-testid="retry-button">Retry</button>
    </div>
  ),
}));

vi.mock('../DocumentDetails', () => ({
  DocumentDetails: ({ documentId, onClose }: { documentId: string; onClose: () => void }) => (
    <div data-testid="document-details" data-document-id={documentId}>
      <button onClick={onClose} data-testid="close-details">Close</button>
    </div>
  ),
}));

const mockDocuments: Document[] = [
  {
    id: '1',
    filename: 'machine-learning.pdf',
    status: 'completed',
    chapter_count: 5,
    figure_count: 10,
    knowledge_count: 25,
    created_at: '2023-01-01T00:00:00Z',
  },
  {
    id: '2',
    filename: 'data-structures.docx',
    status: 'processing',
    chapter_count: 0,
    figure_count: 0,
    knowledge_count: 0,
    created_at: '2023-01-02T00:00:00Z',
  },
  {
    id: '3',
    filename: 'algorithms.md',
    status: 'failed',
    chapter_count: 0,
    figure_count: 0,
    knowledge_count: 0,
    created_at: '2023-01-03T00:00:00Z',
  },
];

describe('DocumentList', () => {
  const mockUseDocuments = vi.mocked(await import('../../hooks/useDocuments')).useDocuments;
  const mockOnDocumentSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      mockUseDocuments.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      } as any);

      render(<DocumentList />);

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(screen.getByTestId('loading-spinner')).toHaveAttribute('data-size', 'lg');
    });
  });

  describe('Error State', () => {
    it('shows error message when there is an error', () => {
      const mockRefetch = vi.fn();
      mockUseDocuments.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        refetch: mockRefetch,
      } as any);

      render(<DocumentList />);

      expect(screen.getByTestId('error-message')).toBeInTheDocument();
      expect(screen.getByText('Failed to load documents')).toBeInTheDocument();
      
      const retryButton = screen.getByTestId('retry-button');
      fireEvent.click(retryButton);
      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no documents', () => {
      mockUseDocuments.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      render(<DocumentList />);

      expect(screen.getByText('No documents')).toBeInTheDocument();
      expect(screen.getByText('Get started by uploading your first document.')).toBeInTheDocument();
    });
  });

  describe('Document List Rendering', () => {
    beforeEach(() => {
      mockUseDocuments.mockReturnValue({
        data: mockDocuments,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);
    });

    it('renders all documents', () => {
      render(<DocumentList />);

      expect(screen.getByText('machine-learning.pdf')).toBeInTheDocument();
      expect(screen.getByText('data-structures.docx')).toBeInTheDocument();
      expect(screen.getByText('algorithms.md')).toBeInTheDocument();
    });

    it('shows correct document metadata', () => {
      render(<DocumentList />);

      // Check first document metadata
      expect(screen.getByText('5 chapters')).toBeInTheDocument();
      expect(screen.getByText('10 figures')).toBeInTheDocument();
      expect(screen.getByText('25 knowledge points')).toBeInTheDocument();
    });

    it('shows correct upload dates', () => {
      render(<DocumentList />);

      expect(screen.getByText('Uploaded 1/1/2023')).toBeInTheDocument();
      expect(screen.getByText('Uploaded 1/2/2023')).toBeInTheDocument();
      expect(screen.getByText('Uploaded 1/3/2023')).toBeInTheDocument();
    });
  });

  describe('Status Indicators', () => {
    beforeEach(() => {
      mockUseDocuments.mockReturnValue({
        data: mockDocuments,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);
    });

    it('shows correct status badges', () => {
      render(<DocumentList />);

      expect(screen.getByText('completed')).toHaveClass('bg-green-100', 'text-green-800');
      expect(screen.getByText('processing')).toHaveClass('bg-yellow-100', 'text-yellow-800');
      expect(screen.getByText('failed')).toHaveClass('bg-red-100', 'text-red-800');
    });

    it('shows correct status icons', () => {
      render(<DocumentList />);

      // Check for SVG elements (status icons)
      const statusIcons = screen.getAllByRole('img', { hidden: true });
      expect(statusIcons.length).toBeGreaterThan(0);
    });
  });

  describe('File Type Icons', () => {
    beforeEach(() => {
      mockUseDocuments.mockReturnValue({
        data: mockDocuments,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);
    });

    it('shows appropriate file type icons', () => {
      render(<DocumentList />);

      // All documents should have file type icons (SVGs)
      const fileIcons = screen.getAllByRole('img', { hidden: true });
      expect(fileIcons.length).toBeGreaterThan(0);
    });
  });

  describe('Browse Button', () => {
    beforeEach(() => {
      mockUseDocuments.mockReturnValue({
        data: mockDocuments,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);
    });

    it('shows browse button only for completed documents with chapters', () => {
      render(<DocumentList />);

      const browseButtons = screen.getAllByText('Browse');
      expect(browseButtons).toHaveLength(1); // Only the completed document should have a browse button
    });

    it('browse button has correct link', () => {
      render(<DocumentList />);

      const browseButton = screen.getByText('Browse');
      expect(browseButton.closest('a')).toHaveAttribute('href', '/documents/1/chapters');
    });

    it('prevents event propagation when browse button is clicked', () => {
      render(<DocumentList onDocumentSelect={mockOnDocumentSelect} />);

      const browseButton = screen.getByText('Browse');
      fireEvent.click(browseButton);

      // Document select should not be called when browse button is clicked
      expect(mockOnDocumentSelect).not.toHaveBeenCalled();
    });
  });

  describe('Document Selection', () => {
    beforeEach(() => {
      mockUseDocuments.mockReturnValue({
        data: mockDocuments,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);
    });

    it('calls onDocumentSelect when document is clicked', () => {
      render(<DocumentList onDocumentSelect={mockOnDocumentSelect} />);

      const documentRow = screen.getByText('machine-learning.pdf').closest('div[class*="cursor-pointer"]');
      fireEvent.click(documentRow!);

      expect(mockOnDocumentSelect).toHaveBeenCalledWith(mockDocuments[0]);
    });

    it('shows document details when document is selected', async () => {
      render(<DocumentList />);

      const documentRow = screen.getByText('machine-learning.pdf').closest('div[class*="cursor-pointer"]');
      fireEvent.click(documentRow!);

      await waitFor(() => {
        expect(screen.getByTestId('document-details')).toBeInTheDocument();
        expect(screen.getByTestId('document-details')).toHaveAttribute('data-document-id', '1');
      });
    });

    it('closes document details when close button is clicked', async () => {
      render(<DocumentList />);

      // Select document
      const documentRow = screen.getByText('machine-learning.pdf').closest('div[class*="cursor-pointer"]');
      fireEvent.click(documentRow!);

      await waitFor(() => {
        expect(screen.getByTestId('document-details')).toBeInTheDocument();
      });

      // Close details
      const closeButton = screen.getByTestId('close-details');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('document-details')).not.toBeInTheDocument();
      });
    });
  });

  describe('Hover Effects', () => {
    beforeEach(() => {
      mockUseDocuments.mockReturnValue({
        data: mockDocuments,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);
    });

    it('applies hover styles to document rows', () => {
      render(<DocumentList />);

      const documentRows = screen.getAllByRole('listitem');
      documentRows.forEach(row => {
        const clickableDiv = row.querySelector('div[class*="hover:bg-gray-50"]');
        expect(clickableDiv).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      mockUseDocuments.mockReturnValue({
        data: mockDocuments,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);
    });

    it('has proper list structure', () => {
      render(<DocumentList />);

      expect(screen.getByRole('list')).toBeInTheDocument();
      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(mockDocuments.length);
    });

    it('has accessible document information', () => {
      render(<DocumentList />);

      // Check that document names are properly labeled
      mockDocuments.forEach(doc => {
        expect(screen.getByText(doc.filename)).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles documents with zero counts', () => {
      const documentsWithZeroCounts = [
        {
          ...mockDocuments[0],
          chapter_count: 0,
          figure_count: 0,
          knowledge_count: 0,
        },
      ];

      mockUseDocuments.mockReturnValue({
        data: documentsWithZeroCounts,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      render(<DocumentList />);

      expect(screen.getByText('0 chapters')).toBeInTheDocument();
      expect(screen.getByText('0 figures')).toBeInTheDocument();
      expect(screen.getByText('0 knowledge points')).toBeInTheDocument();
    });

    it('handles documents with unknown file extensions', () => {
      const documentsWithUnknownExt = [
        {
          ...mockDocuments[0],
          filename: 'document.xyz',
        },
      ];

      mockUseDocuments.mockReturnValue({
        data: documentsWithUnknownExt,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      expect(() => {
        render(<DocumentList />);
      }).not.toThrow();

      expect(screen.getByText('document.xyz')).toBeInTheDocument();
    });

    it('handles invalid dates gracefully', () => {
      const documentsWithInvalidDate = [
        {
          ...mockDocuments[0],
          created_at: 'invalid-date',
        },
      ];

      mockUseDocuments.mockReturnValue({
        data: documentsWithInvalidDate,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      expect(() => {
        render(<DocumentList />);
      }).not.toThrow();
    });
  });
});