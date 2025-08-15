import React, { useState, useEffect } from 'react';
import { 
  FunnelIcon, 
  XMarkIcon, 
  ChevronDownIcon,
  ChevronUpIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { SearchFilters as SearchFiltersType, SearchOptions } from '../hooks/useSearch';

interface SearchFiltersProps {
  filters: SearchFiltersType;
  options: SearchOptions;
  onFiltersChange: (filters: Partial<SearchFiltersType>) => void;
  onOptionsChange: (options: Partial<SearchOptions>) => void;
  onClearFilters: () => void;
  isAdvanced: boolean;
  onToggleAdvanced: () => void;
}

export function SearchFilters({
  filters,
  options,
  onFiltersChange,
  onOptionsChange,
  onClearFilters,
  isAdvanced,
  onToggleAdvanced,
}: SearchFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Fetch available documents for filtering
  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.getDocuments(),
  });

  // Fetch available chapters for filtering
  const { data: allChapters } = useQuery({
    queryKey: ['all-chapters'],
    queryFn: async () => {
      if (!documents || documents.length === 0) return [];
      
      const chaptersPromises = documents.map((doc: any) =>
        apiClient.getChapters(doc.id).then(chapters => 
          chapters.map((chapter: any) => ({
            ...chapter,
            document_title: doc.filename,
          }))
        )
      );
      
      const allChapters = await Promise.all(chaptersPromises);
      return allChapters.flat();
    },
    enabled: !!documents && documents.length > 0,
  });

  const knowledgeTypes = [
    { value: 'definition', label: 'Definition' },
    { value: 'fact', label: 'Fact' },
    { value: 'theorem', label: 'Theorem' },
    { value: 'process', label: 'Process' },
    { value: 'example', label: 'Example' },
  ];

  const cardTypes = [
    { value: 'qa', label: 'Q&A Cards' },
    { value: 'cloze', label: 'Cloze Deletion' },
    { value: 'image_hotspot', label: 'Image Hotspot' },
  ];

  const searchTypes = [
    { value: 'hybrid', label: 'Hybrid (Recommended)', description: 'Combines text and semantic search' },
    { value: 'full_text', label: 'Full Text', description: 'Traditional keyword search' },
    { value: 'semantic', label: 'Semantic', description: 'AI-powered meaning search' },
  ];

  const hasActiveFilters = () => {
    return (
      (filters.chapter_ids && filters.chapter_ids.length > 0) ||
      (filters.knowledge_types && filters.knowledge_types.length > 0) ||
      (filters.card_types && filters.card_types.length > 0) ||
      (filters.document_ids && filters.document_ids.length > 0) ||
      filters.difficulty_min !== undefined ||
      filters.difficulty_max !== undefined
    );
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.chapter_ids && filters.chapter_ids.length > 0) count++;
    if (filters.knowledge_types && filters.knowledge_types.length > 0) count++;
    if (filters.card_types && filters.card_types.length > 0) count++;
    if (filters.document_ids && filters.document_ids.length > 0) count++;
    if (filters.difficulty_min !== undefined || filters.difficulty_max !== undefined) count++;
    return count;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-900">Filters</span>
            {hasActiveFilters() && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {getActiveFilterCount()} active
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={onToggleAdvanced}
              className="inline-flex items-center px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <AdjustmentsHorizontalIcon className="h-3 w-3 mr-1" />
              {isAdvanced ? 'Simple' : 'Advanced'}
            </button>
            
            {hasActiveFilters() && (
              <button
                type="button"
                onClick={onClearFilters}
                className="inline-flex items-center px-3 py-1 text-xs font-medium text-red-700 bg-red-100 rounded-md hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                <XMarkIcon className="h-3 w-3 mr-1" />
                Clear
              </button>
            )}
            
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              {isExpanded ? (
                <ChevronUpIcon className="h-4 w-4" />
              ) : (
                <ChevronDownIcon className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* Search Type (Advanced) */}
          {isAdvanced && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Type
              </label>
              <div className="space-y-2">
                {searchTypes.map((type) => (
                  <label key={type.value} className="flex items-start">
                    <input
                      type="radio"
                      name="search_type"
                      value={type.value}
                      checked={options.search_type === type.value}
                      onChange={(e) => onOptionsChange({ search_type: e.target.value as any })}
                      className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <div className="ml-2">
                      <span className="text-sm font-medium text-gray-900">{type.label}</span>
                      <p className="text-xs text-gray-500">{type.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Document Filter */}
          {documents && documents.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Documents
              </label>
              <select
                multiple
                value={filters.document_ids || []}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  onFiltersChange({ document_ids: values.length > 0 ? values : undefined });
                }}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                size={Math.min(documents.length, 4)}
              >
                {documents.map((doc: any) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.filename}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Hold Ctrl/Cmd to select multiple documents
              </p>
            </div>
          )}

          {/* Chapter Filter */}
          {allChapters && allChapters.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Chapters
              </label>
              <select
                multiple
                value={filters.chapter_ids || []}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  onFiltersChange({ chapter_ids: values.length > 0 ? values : undefined });
                }}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                size={Math.min(allChapters.length, 6)}
              >
                {allChapters.map((chapter: any) => (
                  <option key={chapter.id} value={chapter.id}>
                    {chapter.document_title} - {chapter.title}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Hold Ctrl/Cmd to select multiple chapters
              </p>
            </div>
          )}

          {/* Knowledge Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Knowledge Types
            </label>
            <div className="space-y-2">
              {knowledgeTypes.map((type) => (
                <label key={type.value} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.knowledge_types?.includes(type.value) || false}
                    onChange={(e) => {
                      const current = filters.knowledge_types || [];
                      const updated = e.target.checked
                        ? [...current, type.value]
                        : current.filter(t => t !== type.value);
                      onFiltersChange({ 
                        knowledge_types: updated.length > 0 ? updated : undefined 
                      });
                    }}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-900">{type.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Card Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Card Types
            </label>
            <div className="space-y-2">
              {cardTypes.map((type) => (
                <label key={type.value} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.card_types?.includes(type.value) || false}
                    onChange={(e) => {
                      const current = filters.card_types || [];
                      const updated = e.target.checked
                        ? [...current, type.value]
                        : current.filter(t => t !== type.value);
                      onFiltersChange({ 
                        card_types: updated.length > 0 ? updated : undefined 
                      });
                    }}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-900">{type.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Difficulty Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Difficulty Range
            </label>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Minimum</label>
                <select
                  value={filters.difficulty_min || ''}
                  onChange={(e) => {
                    const value = e.target.value ? parseFloat(e.target.value) : undefined;
                    onFiltersChange({ difficulty_min: value });
                  }}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="">Any</option>
                  <option value="0">0 (Easiest)</option>
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4</option>
                  <option value="5">5 (Hardest)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Maximum</label>
                <select
                  value={filters.difficulty_max || ''}
                  onChange={(e) => {
                    const value = e.target.value ? parseFloat(e.target.value) : undefined;
                    onFiltersChange({ difficulty_max: value });
                  }}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="">Any</option>
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4</option>
                  <option value="5">5 (Hardest)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Advanced Options */}
          {isAdvanced && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Results per page
                </label>
                <select
                  value={options.limit || 20}
                  onChange={(e) => onOptionsChange({ limit: parseInt(e.target.value) })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="10">10</option>
                  <option value="20">20</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Similarity threshold ({((options.similarity_threshold || 0.7) * 100).toFixed(0)}%)
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="1.0"
                  step="0.05"
                  value={options.similarity_threshold || 0.7}
                  onChange={(e) => onOptionsChange({ similarity_threshold: parseFloat(e.target.value) })}
                  className="block w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Less strict (50%)</span>
                  <span>More strict (100%)</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Higher values return more precise but fewer results
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}