import React, { useState } from 'react';
import { DocumentUpload } from './DocumentUpload';
import { ErrorMessage } from './ErrorMessage';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess?: (documentId: string) => void;
}

export function UploadModal({ isOpen, onClose, onUploadSuccess }: UploadModalProps) {
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedDocumentId, setUploadedDocumentId] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleUploadSuccess = (documentId: string) => {
    setUploadedDocumentId(documentId);
    setUploadError(null);
    onUploadSuccess?.(documentId);
    
    // Auto-close after showing success message
    setTimeout(() => {
      onClose();
      setUploadedDocumentId(null);
    }, 2000);
  };

  const handleUploadError = (error: string) => {
    setUploadError(error);
    setUploadedDocumentId(null);
  };

  const handleClose = () => {
    setUploadError(null);
    setUploadedDocumentId(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={handleClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div className="absolute top-0 right-0 pt-4 pr-4">
            <button
              type="button"
              onClick={handleClose}
              className="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="sm:flex sm:items-start">
            <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Upload Document
              </h3>

              {uploadError && (
                <div className="mb-4">
                  <ErrorMessage
                    message={uploadError}
                    onRetry={() => setUploadError(null)}
                  />
                </div>
              )}

              {uploadedDocumentId && (
                <div className="mb-4 p-4 bg-green-50 rounded-md">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-green-800">
                        Upload successful!
                      </h3>
                      <div className="mt-2 text-sm text-green-700">
                        <p>Your document has been uploaded and is being processed.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <DocumentUpload
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />

              <div className="mt-4 text-xs text-gray-500">
                <p>
                  Supported formats: PDF, DOCX, Markdown (.md)
                  <br />
                  Maximum file size: 50MB
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}