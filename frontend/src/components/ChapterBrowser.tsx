import React, { useState } from 'react';
import { TableOfContents } from './TableOfContents';
import { ChapterDetail } from './ChapterDetail';
import { useTableOfContents } from '../hooks/useChapters';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

interface ChapterBrowserProps {
  documentId: string;
  onClose?: () => void;
}

export function ChapterBrowser({ documentId, onClose }: ChapterBrowserProps) {
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const { data: toc, isLoading, error } = useTableOfContents(documentId);

  // Auto-select first chapter when TOC loads
  React.useEffect(() => {
    if (toc && toc.chapters.length > 0 && !selectedChapterId) {
      setSelectedChapterId(toc.chapters[0].id);
    }
  }, [toc, selectedChapterId]);

  const selectedChapter = toc?.chapters.find(ch => ch.id === selectedChapterId);

  const handleChapterSelect = (chapterId: string) => {
    setSelectedChapterId(chapterId);
    setIsMobileMenuOpen(false); // Close mobile menu when chapter is selected
  };

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
        message="Failed to load chapter information"
        onRetry={() => window.location.reload()}
      />
    );
  }

  if (!toc || toc.chapters.length === 0) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-gray-900">No chapters found</h3>
        <p className="mt-2 text-sm text-gray-500">
          This document doesn't have any chapters or the processing is still in progress.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col lg:flex-row bg-gray-50">
      {/* Mobile Header */}
      <div className="lg:hidden bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-900 truncate">
            {toc.document_title}
          </h1>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Sidebar - Table of Contents */}
      <div className={`
        lg:w-80 lg:flex-shrink-0 bg-white border-r border-gray-200
        ${isMobileMenuOpen ? 'block' : 'hidden lg:block'}
      `}>
        <div className="h-full flex flex-col">
          {/* Desktop Header */}
          <div className="hidden lg:flex items-center justify-between px-4 py-4 border-b border-gray-200">
            <h1 className="text-lg font-semibold text-gray-900 truncate">
              {toc.document_title}
            </h1>
            {onClose && (
              <button
                onClick={onClose}
                className="p-1 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Table of Contents */}
          <div className="flex-1 overflow-hidden">
            <TableOfContents
              documentId={documentId}
              onChapterSelect={handleChapterSelect}
              selectedChapterId={selectedChapterId || undefined}
            />
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {selectedChapter ? (
          <div className="flex-1 overflow-auto p-4 lg:p-6">
            <ChapterDetail
              chapterId={selectedChapter.id}
              chapterTitle={selectedChapter.title}
            />
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900">Select a chapter</h3>
              <p className="mt-2 text-sm text-gray-500">
                Choose a chapter from the table of contents to view its content.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 z-40 bg-black bg-opacity-25"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </div>
  );
}