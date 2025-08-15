import React, { useCallback, useState, useRef, DragEvent } from 'react';
import { useUploadDocument } from '../hooks/useDocuments';
import { LoadingSpinner } from './LoadingSpinner';

interface DocumentUploadProps {
  onUploadSuccess?: (documentId: string) => void;
  onUploadError?: (error: string) => void;
}

export function DocumentUpload({ onUploadSuccess, onUploadError }: DocumentUploadProps) {
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isDragReject, setIsDragReject] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadDocument();

  const validateFile = (file: File): string | null => {
    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/markdown',
      'text/plain'
    ];

    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.md')) {
      return 'Unsupported file type. Please upload PDF, DOCX, or Markdown files.';
    }

    // Validate file size (50MB limit)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      return 'File too large. Maximum size is 50MB.';
    }

    return null;
  };

  const handleFileUpload = useCallback(async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      onUploadError?.(validationError);
      return;
    }

    try {
      setUploadProgress(0);
      
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev === null) return 0;
          if (prev >= 90) return prev;
          return prev + Math.random() * 10;
        });
      }, 200);

      const result = await uploadMutation.mutateAsync(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setTimeout(() => {
        setUploadProgress(null);
        onUploadSuccess?.(result.id);
      }, 500);
      
    } catch (error) {
      setUploadProgress(null);
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      onUploadError?.(errorMessage);
    }
  }, [uploadMutation, onUploadSuccess, onUploadError]);

  const handleDragEnter = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
    
    // Check if dragged items contain valid files
    const items = Array.from(e.dataTransfer.items);
    const hasValidFile = items.some(item => {
      if (item.kind === 'file') {
        const file = item.getAsFile();
        return file && validateFile(file) === null;
      }
      return false;
    });
    
    setIsDragReject(!hasValidFile);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    setIsDragReject(false);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    setIsDragReject(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleClick = () => {
    if (uploadProgress === null) {
      fileInputRef.current?.click();
    }
  };

  const isUploading = uploadProgress !== null;

  return (
    <div className="w-full">
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragActive && !isDragReject ? 'border-blue-400 bg-blue-50' : ''}
          ${isDragReject ? 'border-red-400 bg-red-50' : ''}
          ${!isDragActive && !isDragReject ? 'border-gray-300 hover:border-gray-400' : ''}
          ${isUploading ? 'pointer-events-none opacity-50' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.md,.txt"
          onChange={handleFileInputChange}
          className="hidden"
        />
        
        {isUploading ? (
          <div className="space-y-4">
            <LoadingSpinner size="lg" className="mx-auto" />
            <div>
              <p className="text-sm font-medium text-gray-900">Uploading...</p>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">{Math.round(uploadProgress)}% complete</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            
            <div>
              <p className="text-sm font-medium text-gray-900">
                {isDragActive
                  ? isDragReject
                    ? 'File type not supported'
                    : 'Drop your document here'
                  : 'Upload a document'
                }
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {isDragActive
                  ? ''
                  : 'Drag and drop or click to select • PDF, DOCX, Markdown • Max 50MB'
                }
              </p>
            </div>
            
            {!isDragActive && (
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Choose File
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}