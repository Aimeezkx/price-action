import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../../test/utils';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { UploadModal } from '../UploadModal';
import { createMockFile, createMockDragEvent } from '../../test/utils';

// Mock the useUploadDocument hook
vi.mock('../../hooks/useDocuments', () => ({
  useUploadDocument: vi.fn(),
}));

describe('UploadModal', () => {
  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();
  const mockMutate = vi.fn();
  const mockReset = vi.fn();

  const mockUploadMutation = {
    mutate: mockMutate,
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
    data: null,
    reset: mockReset,
  };

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onSuccess: mockOnSuccess,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    const { useUploadDocument } = vi.mocked(await import('../../hooks/useDocuments'));
    useUploadDocument.mockReturnValue(mockUploadMutation);
  });

  describe('Basic Rendering', () => {
    it('renders modal when open', () => {
      render(<UploadModal {...defaultProps} />);

      expect(screen.getByText('Upload Document')).toBeInTheDocument();
      expect(screen.getByText('Choose a file or drag and drop')).toBeInTheDocument();
    });

    it('does not render when closed', () => {
      render(<UploadModal {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Upload Document')).not.toBeInTheDocument();
    });

    it('renders file input', () => {
      render(<UploadModal {...defaultProps} />);

      expect(screen.getByLabelText(/choose file/i)).toBeInTheDocument();
    });

    it('renders supported file types', () => {
      render(<UploadModal {...defaultProps} />);

      expect(screen.getByText(/PDF, DOCX, MD/)).toBeInTheDocument();
    });
  });

  describe('File Selection', () => {
    it('handles file selection via input', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const file = createMockFile('test.pdf', 1024 * 1024, 'application/pdf');
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, file);

      expect(screen.getByText('test.pdf')).toBeInTheDocument();
      expect(screen.getByText('1.0 MB')).toBeInTheDocument();
    });

    it('handles drag and drop', async () => {
      render(<UploadModal {...defaultProps} />);

      const file = createMockFile('document.docx', 2048 * 1024, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
      const dragEvent = createMockDragEvent([file]);

      const dropZone = screen.getByText('Choose a file or drag and drop').closest('div');
      
      fireEvent.dragOver(dropZone!, dragEvent);
      fireEvent.drop(dropZone!, dragEvent);

      await waitFor(() => {
        expect(screen.getByText('document.docx')).toBeInTheDocument();
        expect(screen.getByText('2.0 MB')).toBeInTheDocument();
      });
    });

    it('shows drag over state', () => {
      render(<UploadModal {...defaultProps} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const dragEvent = createMockDragEvent([file]);

      const dropZone = screen.getByText('Choose a file or drag and drop').closest('div');
      
      fireEvent.dragEnter(dropZone!, dragEvent);

      expect(dropZone).toHaveClass('border-blue-400', 'bg-blue-50');
    });

    it('removes drag over state on drag leave', () => {
      render(<UploadModal {...defaultProps} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const dragEvent = createMockDragEvent([file]);

      const dropZone = screen.getByText('Choose a file or drag and drop').closest('div');
      
      fireEvent.dragEnter(dropZone!, dragEvent);
      fireEvent.dragLeave(dropZone!, dragEvent);

      expect(dropZone).not.toHaveClass('border-blue-400', 'bg-blue-50');
    });
  });

  describe('File Validation', () => {
    it('accepts valid file types', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const validFiles = [
        createMockFile('test.pdf', 1024, 'application/pdf'),
        createMockFile('test.docx', 1024, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        createMockFile('test.md', 1024, 'text/markdown'),
      ];

      const input = screen.getByLabelText(/choose file/i);

      for (const file of validFiles) {
        await user.upload(input, file);
        expect(screen.getByText(file.name)).toBeInTheDocument();
        
        // Clear for next test
        const removeButton = screen.getByLabelText('Remove file');
        await user.click(removeButton);
      }
    });

    it('rejects invalid file types', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const invalidFile = createMockFile('test.txt', 1024, 'text/plain');
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, invalidFile);

      expect(screen.getByText(/Please select a valid file type/)).toBeInTheDocument();
      expect(screen.queryByText('test.txt')).not.toBeInTheDocument();
    });

    it('rejects files that are too large', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const largeFile = createMockFile('large.pdf', 100 * 1024 * 1024, 'application/pdf'); // 100MB
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, largeFile);

      expect(screen.getByText(/File size must be less than/)).toBeInTheDocument();
      expect(screen.queryByText('large.pdf')).not.toBeInTheDocument();
    });

    it('shows file size in human readable format', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const files = [
        { file: createMockFile('small.pdf', 512, 'application/pdf'), expectedSize: '512 B' },
        { file: createMockFile('medium.pdf', 1536, 'application/pdf'), expectedSize: '1.5 KB' },
        { file: createMockFile('large.pdf', 2.5 * 1024 * 1024, 'application/pdf'), expectedSize: '2.5 MB' },
      ];

      const input = screen.getByLabelText(/choose file/i);

      for (const { file, expectedSize } of files) {
        await user.upload(input, file);
        expect(screen.getByText(expectedSize)).toBeInTheDocument();
        
        // Clear for next test
        const removeButton = screen.getByLabelText('Remove file');
        await user.click(removeButton);
      }
    });
  });

  describe('File Upload', () => {
    it('uploads file when upload button is clicked', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, file);

      const uploadButton = screen.getByRole('button', { name: 'Upload' });
      await user.click(uploadButton);

      expect(mockMutate).toHaveBeenCalledWith(file);
    });

    it('disables upload button when no file selected', () => {
      render(<UploadModal {...defaultProps} />);

      const uploadButton = screen.getByRole('button', { name: 'Upload' });
      expect(uploadButton).toBeDisabled();
    });

    it('shows loading state during upload', () => {
      const uploadingMutation = { ...mockUploadMutation, isPending: true };
      const { useUploadDocument } = vi.mocked(require('../../hooks/useDocuments'));
      useUploadDocument.mockReturnValue(uploadingMutation);

      render(<UploadModal {...defaultProps} />);

      expect(screen.getByText('Uploading...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /uploading/i })).toBeDisabled();
    });

    it('shows success state after upload', () => {
      const successMutation = { 
        ...mockUploadMutation, 
        isSuccess: true,
        data: { id: '1', filename: 'test.pdf', status: 'processing' }
      };
      const { useUploadDocument } = vi.mocked(require('../../hooks/useDocuments'));
      useUploadDocument.mockReturnValue(successMutation);

      render(<UploadModal {...defaultProps} />);

      expect(screen.getByText('Upload successful!')).toBeInTheDocument();
      expect(screen.getByText('Your document is being processed.')).toBeInTheDocument();
    });

    it('shows error state on upload failure', () => {
      const errorMutation = { 
        ...mockUploadMutation, 
        isError: true,
        error: new Error('Upload failed')
      };
      const { useUploadDocument } = vi.mocked(require('../../hooks/useDocuments'));
      useUploadDocument.mockReturnValue(errorMutation);

      render(<UploadModal {...defaultProps} />);

      expect(screen.getByText('Upload failed')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument();
    });

    it('allows retry after upload failure', async () => {
      const user = userEvent.setup();
      const errorMutation = { 
        ...mockUploadMutation, 
        isError: true,
        error: new Error('Upload failed')
      };
      const { useUploadDocument } = vi.mocked(require('../../hooks/useDocuments'));
      useUploadDocument.mockReturnValue(errorMutation);

      render(<UploadModal {...defaultProps} />);

      const retryButton = screen.getByRole('button', { name: 'Try Again' });
      await user.click(retryButton);

      expect(mockReset).toHaveBeenCalled();
    });
  });

  describe('File Management', () => {
    it('allows removing selected file', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, file);
      expect(screen.getByText('test.pdf')).toBeInTheDocument();

      const removeButton = screen.getByLabelText('Remove file');
      await user.click(removeButton);

      expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Upload' })).toBeDisabled();
    });

    it('shows file preview with correct icon', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, file);

      // Should show PDF icon
      const fileIcon = screen.getByRole('img', { hidden: true });
      expect(fileIcon).toBeInTheDocument();
    });
  });

  describe('Modal Behavior', () => {
    it('closes modal when close button is clicked', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const closeButton = screen.getByLabelText('Close');
      await user.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('closes modal when clicking outside', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const backdrop = screen.getByRole('dialog').parentElement;
      await user.click(backdrop!);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('closes modal on escape key', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      await user.keyboard('{Escape}');

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('calls onSuccess after successful upload', () => {
      const successMutation = { 
        ...mockUploadMutation, 
        isSuccess: true,
        data: { id: '1', filename: 'test.pdf', status: 'processing' }
      };
      const { useUploadDocument } = vi.mocked(require('../../hooks/useDocuments'));
      useUploadDocument.mockReturnValue(successMutation);

      render(<UploadModal {...defaultProps} />);

      expect(mockOnSuccess).toHaveBeenCalledWith(successMutation.data);
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<UploadModal {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('traps focus within modal', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const closeButton = screen.getByLabelText('Close');
      const fileInput = screen.getByLabelText(/choose file/i);

      // Focus should be trapped within modal
      closeButton.focus();
      expect(document.activeElement).toBe(closeButton);

      await user.tab();
      expect(document.activeElement).toBe(fileInput);
    });

    it('has proper labels for screen readers', () => {
      render(<UploadModal {...defaultProps} />);

      expect(screen.getByLabelText(/choose file/i)).toBeInTheDocument();
      expect(screen.getByLabelText('Close')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('adapts to mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<UploadModal {...defaultProps} />);

      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();
      
      // Modal should be responsive
      expect(modal.closest('.sm\\:max-w-lg')).toBeInTheDocument();
    });
  });

  describe('Progress Indication', () => {
    it('shows upload progress when available', () => {
      const uploadingMutation = { 
        ...mockUploadMutation, 
        isPending: true,
        // In a real implementation, this might include progress
      };
      const { useUploadDocument } = vi.mocked(require('../../hooks/useDocuments'));
      useUploadDocument.mockReturnValue(uploadingMutation);

      render(<UploadModal {...defaultProps} />);

      expect(screen.getByText('Uploading...')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles multiple file selection (takes first file)', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const files = [
        createMockFile('first.pdf', 1024, 'application/pdf'),
        createMockFile('second.pdf', 1024, 'application/pdf'),
      ];
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, files);

      // Should only show first file
      expect(screen.getByText('first.pdf')).toBeInTheDocument();
      expect(screen.queryByText('second.pdf')).not.toBeInTheDocument();
    });

    it('handles empty file selection', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const input = screen.getByLabelText(/choose file/i);
      
      // Simulate selecting no files
      Object.defineProperty(input, 'files', {
        value: [],
        writable: false,
      });

      fireEvent.change(input);

      expect(screen.getByRole('button', { name: 'Upload' })).toBeDisabled();
    });

    it('handles file with no extension', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />);

      const file = createMockFile('document', 1024, 'application/pdf');
      const input = screen.getByLabelText(/choose file/i);

      await user.upload(input, file);

      expect(screen.getByText('document')).toBeInTheDocument();
    });
  });
});