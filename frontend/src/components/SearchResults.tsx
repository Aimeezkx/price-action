import React from 'react';
import { 
  DocumentTextIcon, 
  AcademicCapIcon, 
  ChartBarIcon,
  ClockIcon,
  TagIcon,
  BookOpenIcon
} from '@heroicons/react/24/outline';
import { SearchResult } from '../types';

interface SearchResultsProps {
  results: SearchResult[];
  totalResults: number;
  query: string;
  isLoading?: boolean;
  onResultClick?: (result: SearchResult) => void;
}

export function SearchResults({
  results,
  totalResults,
  query,
  isLoading = false,
  onResultClick,
}: SearchResultsProps) {
  // Highlight search terms in text
  const highlightText = (text: string, highlights?: string[]) => {
    if (!highlights || highlights.length === 0) {
      // Fallback: highlight query terms
      const terms = query.toLowerCase().split(/\s+/).filter(term => term.length > 2);
      if (terms.length === 0) return text;
      
      const regex = new RegExp(`(${terms.join('|')})`, 'gi');
      const parts = text.split(regex);
      
      return parts.map((part, index) => {
        const isHighlight = terms.some(term => 
          part.toLowerCase() === term.toLowerCase()
        );
        return isHighlight ? (
          <mark key={index} className="bg-yellow-200 px-1 rounded">
            {part}
          </mark>
        ) : (
          part
        );
      });
    }

    // Use provided highlights
    let highlightedText = text;
    highlights.forEach(highlight => {
      const regex = new RegExp(`(${highlight})`, 'gi');
      highlightedText = highlightedText.replace(
        regex,
        '<mark class="bg-yellow-200 px-1 rounded">$1</mark>'
      );
    });

    return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />;
  };

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'knowledge':
        return <DocumentTextIcon className="h-5 w-5 text-blue-500" />;
      case 'card':
        return <AcademicCapIcon className="h-5 w-5 text-green-500" />;
      default:
        return <BookOpenIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getResultTypeLabel = (type: string) => {
    switch (type) {
      case 'knowledge':
        return 'Knowledge Point';
      case 'card':
        return 'Flashcard';
      default:
        return 'Content';
    }
  };

  const getDifficultyColor = (difficulty?: number) => {
    if (!difficulty) return 'text-gray-500';
    if (difficulty <= 1.5) return 'text-green-600';
    if (difficulty <= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getDifficultyLabel = (difficulty?: number) => {
    if (!difficulty) return 'Unknown';
    if (difficulty <= 1.5) return 'Easy';
    if (difficulty <= 3) return 'Medium';
    return 'Hard';
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, index) => (
          <div key={index} className="animate-pulse">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-start space-x-4">
                <div className="w-5 h-5 bg-gray-300 rounded"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                  <div className="space-y-1">
                    <div className="h-3 bg-gray-300 rounded"></div>
                    <div className="h-3 bg-gray-300 rounded w-5/6"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (results.length === 0 && query) {
    return (
      <div className="text-center py-12">
        <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
        <p className="mt-1 text-sm text-gray-500">
          Try adjusting your search terms or filters to find what you're looking for.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {totalResults > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-600 pb-2 border-b border-gray-200">
          <span>
            {totalResults.toLocaleString()} result{totalResults !== 1 ? 's' : ''} found
          </span>
          <span className="flex items-center">
            <ClockIcon className="h-4 w-4 mr-1" />
            Search completed
          </span>
        </div>
      )}

      {results.map((result) => (
        <div
          key={result.id}
          className="bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all duration-200 cursor-pointer"
          onClick={() => onResultClick?.(result)}
        >
          <div className="p-6">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 mt-1">
                {getResultIcon(result.type)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {getResultTypeLabel(result.type)}
                  </span>
                  
                  {result.metadata?.kind && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      <TagIcon className="h-3 w-3 mr-1" />
                      {result.metadata.kind}
                    </span>
                  )}
                  
                  {result.metadata?.difficulty && (
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDifficultyColor(result.metadata.difficulty)}`}>
                      <ChartBarIcon className="h-3 w-3 mr-1" />
                      {getDifficultyLabel(result.metadata.difficulty)}
                    </span>
                  )}
                  
                  {result.score && (
                    <span className="text-xs text-gray-500">
                      Score: {(result.score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {highlightText(result.title, result.highlights)}
                </h3>
                
                <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                  {highlightText(result.content, result.highlights)}
                </p>
                
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  {result.chapter_title && (
                    <span className="flex items-center">
                      <BookOpenIcon className="h-3 w-3 mr-1" />
                      {result.chapter_title}
                    </span>
                  )}
                  
                  {result.metadata?.anchors?.page && (
                    <span>Page {result.metadata.anchors.page}</span>
                  )}
                  
                  {result.metadata?.entities && result.metadata.entities.length > 0 && (
                    <span className="flex items-center">
                      <TagIcon className="h-3 w-3 mr-1" />
                      {result.metadata.entities.slice(0, 3).join(', ')}
                      {result.metadata.entities.length > 3 && ` +${result.metadata.entities.length - 3} more`}
                    </span>
                  )}
                </div>
                
                {result.metadata?.rank_factors && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <details className="text-xs text-gray-500">
                      <summary className="cursor-pointer hover:text-gray-700">
                        Ranking factors
                      </summary>
                      <div className="mt-2 space-y-1">
                        {Object.entries(result.metadata.rank_factors).map(([factor, score]) => (
                          <div key={factor} className="flex justify-between">
                            <span className="capitalize">{factor.replace('_', ' ')}</span>
                            <span>{(score as number * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}