import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChapterBrowser } from '../components';
import { useDocument } from '../hooks/useDocuments';
import { LoadingSpinner, ErrorMessage } from '../components';

export function ChapterBrowserPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  
  const { data: document, isLoading, error } = useDocument(documentId!);

  if (!documentId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <ErrorMessage message="Document ID is required" />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <ErrorMessage
          message="Failed to load document"
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <ErrorMessage message="Document not found" />
      </div>
    );
  }

  if (document.status !== 'completed') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="mb-4">
            {document.status === 'processing' ? (
              <LoadingSpinner size="lg" />
            ) : (
              <svg className="mx-auto h-12 w-12 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            )}
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {document.status === 'processing' 
              ? 'Document is still processing'
              : document.status === 'failed'
              ? 'Document processing failed'
              : 'Document not ready'
            }
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            {document.status === 'processing'
              ? 'Please wait while we extract chapters and content from your document.'
              : document.status === 'failed'
              ? 'There was an error processing your document. Please try uploading again.'
              : 'This document is not ready for browsing yet.'
            }
          </p>
          <button
            onClick={() => navigate('/documents')}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Back to Documents
          </button>
        </div>
      </div>
    );
  }

  if (document.chapter_count === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No chapters found</h3>
          <p className="mt-2 text-sm text-gray-500 mb-4">
            This document doesn't contain any identifiable chapters or sections.
          </p>
          <button
            onClick={() => navigate('/documents')}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Back to Documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      <ChapterBrowser 
        documentId={documentId} 
        onClose={() => navigate('/documents')}
      />
    </div>
  );
}