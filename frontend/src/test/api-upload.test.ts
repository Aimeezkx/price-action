/**
 * API Upload Response Handling Tests
 * 
 * Tests that the frontend API client can handle upload responses correctly
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { uploadDocument } from '../lib/api';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock file creation helper
const createMockFile = (name: string, type: string, size: number = 1024): File => {
  const content = 'a'.repeat(size);
  return new File([content], name, { type });
};

describe('API Upload Response Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Successful Upload Responses', () => {
    it('should handle successful PDF upload response', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        filename: 'test.pdf',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
        file_type: 'pdf',
        file_size: 1024,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');
      const result = await uploadDocument(testFile);

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ingest'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      );
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

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });

      const testFile = createMockFile('test.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
      const result = await uploadDocument(testFile);

      expect(result).toEqual(mockResponse);
      expect(result.filename).toBe('test.docx');
      expect(result.status).toBe('pending');
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

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });

      const testFile = createMockFile('test.txt', 'text/plain');
      const result = await uploadDocument(testFile);

      expect(result).toEqual(mockResponse);
      expect(result.file_type).toBe('txt');
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

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });

      const testFile = createMockFile('test.md', 'text/markdown');
      const result = await uploadDocument(testFile);

      expect(result).toEqual(mockResponse);
      expect(result.file_type).toBe('md');
    });
  });

  describe('Error Response Handling', () => {
    it('should handle invalid file type error (400)', async () => {
      const mockErrorResponse = {
        error: 'file_validation_failed',
        message: 'File failed security validation.',
        issues: ['Invalid file extension'],
        allowed_extensions: ['.pdf', '.docx', '.txt', '.md'],
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => mockErrorResponse,
      });

      const testFile = createMockFile('test.exe', 'application/octet-stream');

      await expect(uploadDocument(testFile)).rejects.toThrow();
    });

    it('should handle file too large error (413)', async () => {
      const mockErrorResponse = {
        error: 'file_too_large',
        message: 'File size exceeds maximum allowed size.',
        max_size_bytes: 10485760,
        file_size_bytes: 15728640,
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 413,
        json: async () => mockErrorResponse,
      });

      const testFile = createMockFile('large.pdf', 'application/pdf', 15728640);

      await expect(uploadDocument(testFile)).rejects.toThrow();
    });

    it('should handle empty file error (400)', async () => {
      const mockErrorResponse = {
        error: 'empty_file',
        message: 'File is empty. Please upload a file with content.',
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => mockErrorResponse,
      });

      const testFile = createMockFile('empty.pdf', 'application/pdf', 0);

      await expect(uploadDocument(testFile)).rejects.toThrow();
    });

    it('should handle server error (500)', async () => {
      const mockErrorResponse = {
        error: 'internal_server_error',
        message: 'An unexpected error occurred while processing your upload.',
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => mockErrorResponse,
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');

      await expect(uploadDocument(testFile)).rejects.toThrow();
    });

    it('should handle network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network Error'));

      const testFile = createMockFile('test.pdf', 'application/pdf');

      await expect(uploadDocument(testFile)).rejects.toThrow('Network Error');
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

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');
      const result = await uploadDocument(testFile);

      // Verify all fields are present
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('filename');
      expect(result).toHaveProperty('status');
      expect(result).toHaveProperty('created_at');
      expect(result).toHaveProperty('updated_at');
      expect(result).toHaveProperty('file_type');
      expect(result).toHaveProperty('file_size');
      expect(result).toHaveProperty('error_message');

      // Verify field types
      expect(typeof result.id).toBe('string');
      expect(typeof result.filename).toBe('string');
      expect(typeof result.status).toBe('string');
      expect(typeof result.created_at).toBe('string');
      expect(typeof result.file_size).toBe('number');
    });

    it('should handle response with minimal required fields', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        filename: 'test.pdf',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');
      const result = await uploadDocument(testFile);

      // Verify minimal required fields are present
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('filename');
      expect(result).toHaveProperty('status');
      expect(result).toHaveProperty('created_at');

      // Verify field values
      expect(result.id).toBe('123e4567-e89b-12d3-a456-426614174000');
      expect(result.filename).toBe('test.pdf');
      expect(result.status).toBe('pending');
    });

    it('should handle different status values', async () => {
      const statusValues = ['pending', 'processing', 'completed', 'failed'];

      for (const status of statusValues) {
        const mockResponse = {
          id: '123e4567-e89b-12d3-a456-426614174000',
          filename: 'test.pdf',
          status: status,
          created_at: '2024-01-01T00:00:00Z',
        };

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: async () => mockResponse,
        });

        const testFile = createMockFile('test.pdf', 'application/pdf');
        const result = await uploadDocument(testFile);

        expect(result.status).toBe(status);
      }
    });
  });

  describe('FormData Construction', () => {
    it('should construct FormData correctly for file upload', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        filename: 'test.pdf',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');
      await uploadDocument(testFile);

      // Verify fetch was called with FormData
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ingest'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      );

      // Get the FormData from the call
      const callArgs = mockFetch.mock.calls[0];
      const formData = callArgs[1].body as FormData;
      
      // Verify the file was added to FormData
      expect(formData.get('file')).toBe(testFile);
    });
  });

  describe('HTTP Status Code Handling', () => {
    it('should handle 201 Created status', async () => {
      const mockResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        filename: 'test.pdf',
        status: 'pending',
        created_at: '2024-01-01T00:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');
      const result = await uploadDocument(testFile);

      expect(result).toEqual(mockResponse);
    });

    it('should handle 400 Bad Request status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Bad Request' }),
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');

      await expect(uploadDocument(testFile)).rejects.toThrow();
    });

    it('should handle 413 Payload Too Large status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 413,
        json: async () => ({ error: 'Payload Too Large' }),
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');

      await expect(uploadDocument(testFile)).rejects.toThrow();
    });

    it('should handle 422 Unprocessable Entity status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({ error: 'Unprocessable Entity' }),
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');

      await expect(uploadDocument(testFile)).rejects.toThrow();
    });

    it('should handle 500 Internal Server Error status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal Server Error' }),
      });

      const testFile = createMockFile('test.pdf', 'application/pdf');

      await expect(uploadDocument(testFile)).rejects.toThrow();
    });
  });
});