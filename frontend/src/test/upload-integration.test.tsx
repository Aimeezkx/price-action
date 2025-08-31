/**
 * Frontend Upload Integration Tests
 * 
 * Tests that the frontend can handle upload responses correctly
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentUpload } from '../components/DocumentUpload';
import { uploadDocument } from '../lib/api';

// Mock the API module
vi.mock('../lib/api', () => ({
  uploadDocument: vi.fn(),
}));

const mockUploadDocument = vi.mocked(uploadDocument);

// Test wrapper with QueryClient
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

// Mock file creation helpers
const createMockFile = (name: string, type: string, size: number = 1024): File => {
  const content = 'a'.repeat(size);
  return new File([content], name, { type });
};

describe('Frontend Upload Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Successful Upload Handling', () => {
    it('should handle successful PDF upload response', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        filename: 'test.pdf',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
        file_type: 'pdf',
        file_size: 1024,
      };

      mockUploadDocument.mockResolvedValueOnce(mockResponse);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.pdf', 'application/pdf');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      // Verify success message or state
      await waitFor(() => {
        expect(screen.getByText(/upload successful|uploaded successfully/i)).toBeInTheDocument();
      });
    });

    it('should handle successful DOCX upload response', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174001',
        filename: 'test.docx',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
        file_type: 'docx',
        file_size: 2048,
      };

      mockUploadDocument.mockResolvedValueOnce(mockResponse);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      await waitFor(() => {
        expect(screen.getByText(/upload successful|uploaded successfully/i)).toBeInTheDocument();
      });
    });

    it('should handle successful TXT upload response', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174002',
        filename: 'test.txt',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
        file_type: 'txt',
        file_size: 512,
      };

      mockUploadDocument.mockResolvedValueOnce(mockResponse);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.txt', 'text/plain');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      await waitFor(() => {
        expect(screen.getByText(/upload successful|uploaded successfully/i)).toBeInTheDocument();
      });
    });

    it('should handle successful Markdown upload response', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174003',
        filename: 'test.md',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
        file_type: 'md',
        file_size: 256,
      };

      mockUploadDocument.mockResolvedValueOnce(mockResponse);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.md', 'text/markdown');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      await waitFor(() => {
        expect(screen.getByText(/upload successful|uploaded successfully/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Response Handling', () => {
    it('should handle invalid file type error', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            error: 'file_validation_failed',
            message: 'File failed security validation.',
            issues: ['Invalid file extension'],
            allowed_extensions: ['.pdf', '.docx', '.txt', '.md'],
          },
        },
      };

      mockUploadDocument.mockRejectedValueOnce(mockError);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.exe', 'application/octet-stream');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      // Verify error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/file failed security validation|invalid file/i)).toBeInTheDocument();
      });
    });

    it('should handle file too large error', async () => {
      const mockError = {
        response: {
          status: 413,
          data: {
            error: 'file_too_large',
            message: 'File size exceeds maximum allowed size.',
            max_size_bytes: 10485760,
            file_size_bytes: 15728640,
          },
        },
      };

      mockUploadDocument.mockRejectedValueOnce(mockError);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('large.pdf', 'application/pdf', 15728640);

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      // Verify error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/file size exceeds|too large/i)).toBeInTheDocument();
      });
    });

    it('should handle empty file error', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            error: 'empty_file',
            message: 'File is empty. Please upload a file with content.',
          },
        },
      };

      mockUploadDocument.mockRejectedValueOnce(mockError);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('empty.pdf', 'application/pdf', 0);

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      // Verify error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/file is empty|empty file/i)).toBeInTheDocument();
      });
    });

    it('should handle server error', async () => {
      const mockError = {
        response: {
          status: 500,
          data: {
            error: 'internal_server_error',
            message: 'An unexpected error occurred while processing your upload.',
          },
        },
      };

      mockUploadDocument.mockRejectedValueOnce(mockError);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.pdf', 'application/pdf');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      // Verify error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/server error|unexpected error/i)).toBeInTheDocument();
      });
    });

    it('should handle network error', async () => {
      const mockError = new Error('Network Error');
      mockUploadDocument.mockRejectedValueOnce(mockError);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.pdf', 'application/pdf');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      // Verify error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/network error|connection error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Upload Progress and Status', () => {
    it('should show upload progress during upload', async () => {
      // Mock a delayed response to test progress state
      mockUploadDocument.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            id: '123e4567-e89b-12d3-a456-426614174000',
            filename: 'test.pdf',
            status: 'pending',
            created_at: '2024-01-01T00:00:00Z',
            file_type: 'pdf',
            file_size: 1024,
          }), 1000)
        )
      );

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.pdf', 'application/pdf');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      // Should show uploading state
      await waitFor(() => {
        expect(screen.getByText(/uploading|processing/i)).toBeInTheDocument();
      });

      // Should complete eventually
      await waitFor(() => {
        expect(screen.getByText(/upload successful|uploaded successfully/i)).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should display document status after successful upload', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        filename: 'test.pdf',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
        file_type: 'pdf',
        file_size: 1024,
      };

      mockUploadDocument.mockResolvedValueOnce(mockResponse);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.pdf', 'application/pdf');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      // Should show document status
      await waitFor(() => {
        expect(screen.getByText(/pending|processing/i)).toBeInTheDocument();
      });
    });
  });

  describe('File Validation', () => {
    it('should validate file type before upload', async () => {
      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.exe', 'application/octet-stream');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      // Should show validation error before upload
      await waitFor(() => {
        expect(screen.getByText(/invalid file type|unsupported file/i)).toBeInTheDocument();
      });

      // Upload button should be disabled or not trigger upload
      const uploadButton = screen.getByRole('button', { name: /upload/i });
      expect(uploadButton).toBeDisabled();
    });

    it('should validate file size before upload', async () => {
      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('large.pdf', 'application/pdf', 20 * 1024 * 1024); // 20MB

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      // Should show size validation error
      await waitFor(() => {
        expect(screen.getByText(/file too large|exceeds maximum size/i)).toBeInTheDocument();
      });

      // Upload button should be disabled
      const uploadButton = screen.getByRole('button', { name: /upload/i });
      expect(uploadButton).toBeDisabled();
    });
  });

  describe('Response Format Validation', () => {
    it('should handle response with all required fields', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        filename: 'test.pdf',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        file_type: 'pdf',
        file_size: 1024,
        error_message: null,
      };

      mockUploadDocument.mockResolvedValueOnce(mockResponse);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.pdf', 'application/pdf');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      // Should handle complete response successfully
      await waitFor(() => {
        expect(screen.getByText(/upload successful|uploaded successfully/i)).toBeInTheDocument();
      });
    });

    it('should handle response with minimal required fields', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        filename: 'test.pdf',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
      };

      mockUploadDocument.mockResolvedValueOnce(mockResponse);

      const TestWrapper = createTestWrapper();
      render(
        <TestWrapper>
          <DocumentUpload />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/choose file|upload/i);
      const testFile = createMockFile('test.pdf', 'application/pdf');

      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledWith(testFile);
      });

      // Should handle minimal response successfully
      await waitFor(() => {
        expect(screen.getByText(/upload successful|uploaded successfully/i)).toBeInTheDocument();
      });
    });
  });
});