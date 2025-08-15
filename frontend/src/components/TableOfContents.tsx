import React, { useState } from 'react';
import { useTableOfContents } from '../hooks/useChapters';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';
import type { ChapterTOC } from '../types';

interface TableOfContentsProps {
  documentId: string;
  onChapterSelect: (chapterId: string) => void;
  selectedChapterId?: string;
}

export function TableOfContents({ 
  documentId, 
  onChapterSelect, 
  selectedChapterId 
}: TableOfContentsProps) {
  const { data: toc, isLoading, error, refetch } = useTableOfContents(documentId);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-32">
        <LoadingSpinner size="md" />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load table of contents"
        onRetry={() => refetch()}
      />
    );
  }

  if (!toc || toc.chapters.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No chapters found in this document.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Table of Contents</h3>
        <p className="text-sm text-gray-500 mt-1">
          {toc.total_chapters} chapter{toc.total_chapters !== 1 ? 's' : ''}
        </p>
      </div>
      
      <div className="max-h-96 overflow-y-auto">
        <nav className="py-2">
          {toc.chapters.map((chapter) => (
            <ChapterItem
              key={chapter.id}
              chapter={chapter}
              isSelected={selectedChapterId === chapter.id}
              onClick={() => onChapterSelect(chapter.id)}
            />
          ))}
        </nav>
      </div>
    </div>
  );
}

interface ChapterItemProps {
  chapter: ChapterTOC;
  isSelected: boolean;
  onClick: () => void;
}

function ChapterItem({ chapter, isSelected, onClick }: ChapterItemProps) {
  const getIndentStyle = (level: number) => {
    if (level <= 1) return {};
    const indent = Math.min(level - 1, 6) * 16; // 16px per level
    return { paddingLeft: `${16 + indent}px` };
  };
  
  return (
    <button
      onClick={onClick}
      style={getIndentStyle(chapter.level)}
      className={`
        w-full text-left py-2 hover:bg-gray-50 transition-colors
        ${isSelected ? 'bg-blue-50 border-r-2 border-blue-500' : ''}
        ${chapter.level <= 1 ? 'px-4' : 'pr-4'}
      `}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className={`
            text-sm font-medium truncate
            ${isSelected ? 'text-blue-700' : 'text-gray-900'}
          `}>
            {chapter.title}
          </p>
          
          {(chapter.page_start || chapter.page_end) && (
            <p className="text-xs text-gray-500 mt-1">
              {chapter.page_start && chapter.page_end 
                ? `Pages ${chapter.page_start}-${chapter.page_end}`
                : chapter.page_start 
                ? `Page ${chapter.page_start}+`
                : `Page ${chapter.page_end}`
              }
            </p>
          )}
        </div>
        
        {!chapter.has_content && (
          <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
            Empty
          </span>
        )}
      </div>
    </button>
  );
}