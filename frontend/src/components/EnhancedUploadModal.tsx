/**
 * Enhanced Upload Modal
 * Modal component with advanced upload progress tracking and error handling
 * Supports multiple file uploads with detailed feedback
 */

import React, { useState, useRef, DragEvent } from 'react';
import { useUploadManager } from '../hooks/useUploadManager';
import UploadProgress from './UploadProgress';
import { UploadItem } from '../lib/upload-manager';

export interface EnhancedUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess?: (documentId: string, fileName: string) => void;
  maxFiles?: number;
  allowMultiple?: boolean;
  className?: string;
}

export const EnhancedUploadModal: React.FC<EnhancedUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
  maxFiles = 5,
  allowMultiple = true,
  className = ''
}) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [isDragReject, setIsDragReject] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { 
    uploads, 
    activeUploads, 
    stats, 
    addUpload, 
    cancelUpload, 
    retryUpload, 
    clearCompleted 
  } = useUploadManager();

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

  const handleFileUpload = (files: FileList) => {
    const filesToUpload = Array.from(files).slice(0, maxFiles);
    
    filesToUpload.forEach(file => {
      const validationError = validateFile(file);
      if (validationError) {
        // Could show validation error notification here
        console.error(`Validation error for ${file.name}: ${validationError}`);
        return;
      }

      addUpload(file, {
        onComplete: (item: UploadItem, result: any) => {
          onUploadSuccess?.(result.id, item.file.name);
        }
      });
    });
  };

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

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files);
    }
    // Reset input value to allow selecting the same file again
    e.target.value = '';
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleClose = () => {
    // Cancel any active uploads before closing
    activeUploads.forEach(upload => {
      if (['preparing', 'uploading'].includes(upload.status)) {
        cancelUpload(upload.id);
      }
    });
    onClose();
  };

  const hasActiveUploads = activeUploads.length > 0;
  const hasCompletedUploads = uploads.some(u => u.status === 'success');
  const hasFailedUploads = uploads.some(u => u.status === 'failed');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={handleClose}
        />

        {/* Modal panel */}
        <div className={`inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full ${className}`}>
          {/* Header */}
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Upload Documents
              </h3>
              <button
                onClick={handleClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Upload Stats */}
            {uploads.length > 0 && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between text-sm">
                  <span>
                    {stats.totalUploads} file{stats.totalUploads !== 1 ? 's' : ''} • 
                    {stats.activeUploads} active • 
                    {stats.completedUploads} completed • 
                    {stats.failedUploads} failed
                  </span>
                  {hasCompletedUploads && (
                    <button
                      onClick={clearCompleted}
                      className="text-blue-600 hover:text-blue-800 text-xs"
                    >
                      Clear Completed
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Upload Area */}
          <div className="px-4 sm:px-6">
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
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.md,.txt"
                multiple={allowMultiple}
                onChange={handleFileInputChange}
                className="hidden"
              />
              
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
                        : 'Drop your documents here'
                      : 'Upload documents'
                    }
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {isDragActive
                      ? ''
                      : `Drag and drop or click to select • PDF, DOCX, Markdown • Max 50MB${allowMultiple ? ` • Up to ${maxFiles} files` : ''}`
                    }
                  </p>
                </div>
                
                {!isDragActive && (
                  <button
                    type="button"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Choose Files
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Upload Progress List */}
          {uploads.length > 0 && (
            <div className="px-4 sm:px-6 py-4 max-h-96 overflow-y-auto">
              <div className="space-y-3">
                {uploads.map(upload => (
                  <UploadProgress
                    key={upload.id}
                    status={upload.status}
                    progress={upload.progress}
                    fileName={upload.file.name}
                    fileSize={upload.file.size}
                    uploadSpeed={upload.uploadSpeed}
                    timeRemaining={upload.timeRemaining}
                    error={upload.error?.userMessage}
                    onCancel={() => cancelUpload(upload.id)}
                    onRetry={() => retryUpload(upload.id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={handleClose}
              disabled={hasActiveUploads}
              className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium text-white sm:ml-3 sm:w-auto sm:text-sm ${
                hasActiveUploads
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
              } focus:outline-none focus:ring-2 focus:ring-offset-2`}
            >
              {hasActiveUploads ? 'Uploading...' : 'Done'}
            </button>
            
            {hasActiveUploads && (
              <button
                type="button"
                onClick={() => {
                  activeUploads.forEach(upload => cancelUpload(upload.id));
                }}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel All
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedUploadModal;