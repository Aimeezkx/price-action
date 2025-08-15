import React from 'react';
import { useDocument } from '../hooks/useDocuments';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';
import { ChapterBrowser } from './ChapterBrowser';

interface DocumentDetailsProps {
  documentId: string;
  onClose: () => void;
}

export function DocumentDetails({ documentId, onClose }: DocumentDetailsProps) {
  const { data: document, isLoading, error, refetch } = useDocument(documentId);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load document details"
        onRetry={() => refetch()}
      />
    );
  }

  if (!document) {
    return (
      <ErrorMessage message="Document not found" />
    );
  }

  return (
    <div className="bg-white">
      {/* Header */}
      <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              {document.filename}
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Document details and chapter navigation
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <span className="sr-only">Close</span>
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Document Info */}
      <div className="px-4 py-5 sm:p-6">
        <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd className="mt-1">
              <span
                className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  document.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : document.status === 'processing'
                    ? 'bg-yellow-100 text-yellow-800'
                    : document.status === 'failed'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {document.status}
              </span>
            </dd>
          </div>
          
          <div>
            <dt className="text-sm font-medium text-gray-500">Created</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {new Date(document.created_at).toLocaleDateString()}
            </dd>
          </div>
          
          <div>
            <dt className="text-sm font-medium text-gray-500">Chapters</dt>
            <dd className="mt-1 text-sm text-gray-900">{document.chapter_count}</dd>
          </div>
          
          <div>
            <dt className="text-sm font-medium text-gray-500">Figures</dt>
            <dd className="mt-1 text-sm text-gray-900">{document.figure_count}</dd>
          </div>
          
          <div>
            <dt className="text-sm font-medium text-gray-500">Knowledge Points</dt>
            <dd className="mt-1 text-sm text-gray-900">{document.knowledge_count}</dd>
          </div>
        </dl>

        {/* Processing Status Details */}
        {document.status === 'processing' && (
          <div className="mt-6 p-4 bg-yellow-50 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <LoadingSpinner size="sm" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Processing in progress
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    Your document is being processed. This may take a few minutes depending on the document size.
                    The page will automatically update when processing is complete.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {document.status === 'failed' && (
          <div className="mt-6 p-4 bg-red-50 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Processing failed
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>
                    There was an error processing your document. Please try uploading again or contact support if the problem persists.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Chapter Navigation - Only show if processing is complete */}
        {document.status === 'completed' && document.chapter_count > 0 && (
          <div className="mt-8">
            <h4 className="text-sm font-medium text-gray-900 mb-4">Chapter Navigation</h4>
            <div className="bg-gray-50 rounded-lg p-4">
              <ChapterBrowser documentId={documentId} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

